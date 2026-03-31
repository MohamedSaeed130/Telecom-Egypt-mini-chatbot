"""
Vector Store Manager with Groq LLM and HuggingFace Embeddings
Uses Llama 3 70B via Groq and multilingual-e5-large embeddings
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue,
    SparseVectorParams, SparseIndexParams, SparseVector, Prefetch, Fusion, FusionQuery
)
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from typing import List, Dict, Optional, Any, Union
import numpy as np
from langdetect import detect
import json
import os
from uuid import uuid4
from groq import Groq
import time


class QdrantVectorStoreManager:
    
    def __init__(self, 
                 collection_name: str = "telecom_egypt_VDB",
                 persist_directory: str = "qdrant_db",
                 embedding_model_name: str = "intfloat/multilingual-e5-large",
                 use_cloud: bool = False,
                 qdrant_url: Optional[str] = None,
                 qdrant_api_key: Optional[str] = None,
                 groq_api_key: Optional[str] = None):


        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize Qdrant Client
        if use_cloud and qdrant_url:
            print(f"Connecting to Qdrant Cloud: {qdrant_url}")
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=30
            )
        else:
            print(f"Using local Qdrant storage: {persist_directory}")
            self.client = QdrantClient(path=persist_directory)
        
        # Initialize Groq client for LLM
        groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY is required. Set it in environment or pass as argument.")
        
        self.groq_client = Groq(api_key=groq_key)
        print("Groq client initialized (Llama 3 70B)")
        
        # Load HuggingFace embedding model
        print(f"Loading embedding model: {embedding_model_name}")
        print("First time download may take several minutes (~2 GB model)")
        
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")
        
        self.embedding_model = SentenceTransformer(embedding_model_name, device=device)
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
        
        print(f"Embedding model loaded (dimension: {self.vector_size})")

        # Load Sparse Embedding Model (BM25)
        print("Loading sparse embedding model: Qdrant/bm25")
        self.sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        print("Sparse embedding model loaded")
        
        # Create or get collection
        self._init_collection()
        
        print(f"Vector store initialized. Collection: {collection_name}")
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            lang = detect(text)
            return lang if lang in ['ar', 'en'] else 'en'
        except:
            return "en"

    def _init_collection(self):
        """Initialize or get existing collection. Recreates if config mismatches."""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        should_recreate = False
        if self.collection_name in collection_names:
            # Check if existing collection has compatible config (named vectors + sparse)
            collection_info = self.client.get_collection(self.collection_name)
            vectors_config = collection_info.config.params.vectors
            sparse_vectors_config = collection_info.config.params.sparse_vectors
            
            # Check if 'dense' vector exists and 'bm25' sparse vector exists
            has_dense = isinstance(vectors_config, dict) and 'dense' in vectors_config
            has_sparse = sparse_vectors_config is not None and 'bm25' in sparse_vectors_config
            
            if not (has_dense and has_sparse):
                print(f"Collection '{self.collection_name}' exists but has incompatible config. Recreating...")
                should_recreate = True
        else:
            should_recreate = True
            
        if should_recreate:
            if self.collection_name in collection_names:
                self.client.delete_collection(self.collection_name)
                
            print(f"Creating new collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "bm25": SparseVectorParams(
                        index=SparseIndexParams(
                            on_disk=False,
                        )
                    )
                }
            )
            
            # Ensure payload index exists for 'source' field (required for filtering)
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="source",
                field_schema="keyword",
            )
        else:
            print(f"Collection '{self.collection_name}' already exists with correct config")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using multilingual-e5-large
        Note: E5 models require prefixing with 'query: ' or 'passage: '
        """
        # For E5 models, prefix with 'passage: ' for documents
        # Use 'query: ' for search queries (handled in search method)
        prefixed_texts = [f"passage: {text}" for text in texts]
        
        embeddings = self.embedding_model.encode(
            prefixed_texts,
            show_progress_bar=True,
            normalize_embeddings=True  # Important for cosine similarity
        )
        return embeddings.tolist()
    
    def add_documents(self, documents: List[Dict], batch_size: int = 32):
        """
        Add documents to vector store with dense and sparse vectors
        documents: List of dicts with 'content', 'metadata', and 'id' keys
        """
        total_docs = len(documents)
        print(f"Adding {total_docs} documents to vector store (Dense + Sparse)...")
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract data
            ids = [doc['id'] for doc in batch]
            texts = [doc['content'] for doc in batch]
            metadatas = [doc.get('metadata', {}) for doc in batch]
            
            # Generate Dense embeddings
            # For E5 models, prefix with 'passage: ' for documents
            prefixed_texts = [f"passage: {text}" for text in texts]
            dense_embeddings = self.embedding_model.encode(
                prefixed_texts,
                show_progress_bar=False,
                normalize_embeddings=True
            ).tolist()
            
            # Generate Sparse embeddings (BM25)
            # fastembed returns generator of SparseEmbedding
            sparse_embeddings_gen = self.sparse_embedding_model.embed(texts)
            sparse_embeddings = list(sparse_embeddings_gen)
            
            # Create points for Qdrant
            points = []
            for j, (doc_id, text, dense_emb, sparse_emb, metadata) in enumerate(zip(ids, texts, dense_embeddings, sparse_embeddings, metadatas)):
                # Convert fastembed SparseEmbedding to Qdrant SparseVector
                # fastembed SparseEmbedding has .indices and .values
                qdrant_sparse_vector = SparseVector(
                    indices=sparse_emb.indices.tolist(),
                    values=sparse_emb.values.tolist()
                )
                
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector={
                            "dense": dense_emb,
                            "bm25": qdrant_sparse_vector
                        },
                        payload={
                            'doc_id': doc_id,
                            'content': text,
                            **metadata
                        }
                    )
                )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"Added batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1}")
        
        print(f"✓ Successfully added {total_docs} documents")
    
    def search(self, 
               query: str, 
               n_results: int = 5,
               filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents using Hybrid Retrieval (RRF)
        """
        # 1. Generate Dense Embedding
        # For E5 models, prefix query with 'query: '
        prefixed_query = f"query: {query}"
        query_dense_embedding = self.embedding_model.encode(
            prefixed_query,
            normalize_embeddings=True
        ).tolist()
        
        # 2. Generate Sparse Embedding (BM25)
        # fastembed returns generator
        query_sparse_embedding_gen = self.sparse_embedding_model.embed([query])
        query_sparse_embedding = list(query_sparse_embedding_gen)[0]
        
        qdrant_sparse_vector = SparseVector(
            indices=query_sparse_embedding.indices.tolist(),
            values=query_sparse_embedding.values.tolist()
        )
        
        # 3. Build filter if provided
        query_filter = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)
        
        # 4. Perform Hybrid Search with RRF Fusion
        # Define prefetches for dense and sparse
        prefetch = [
            Prefetch(
                query=query_dense_embedding,
                using="dense",
                limit=n_results,
                filter=query_filter
            ),
            Prefetch(
                query=qdrant_sparse_vector,
                using="bm25",
                limit=n_results,
                filter=query_filter
            ),
        ]
        
        # Execute query with fusion
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=prefetch,
            query=FusionQuery(fusion=Fusion.RRF),
            limit=n_results
        )
        
        # Format results
        formatted_results = []
        for result in search_results.points:
            formatted_results.append({
                'id': result.payload.get('doc_id', str(result.id)),
                'content': result.payload.get('content', ''),
                'metadata': {
                    k: v for k, v in result.payload.items() 
                    if k not in ['doc_id', 'content']
                },
                'score': result.score,
            })
        
        return formatted_results
    
    def generate_response(self, query: str, context_docs: List[Dict], 
                         language: str = 'en',
                         max_tokens: int = 1000,
                         temperature: float = 0.2) -> str:
        """
        Generate response using Groq Llama 3 70B
        
        Args:
            query: User query
            context_docs: Retrieved documents for context
            language: Language of response ('en' or 'ar')
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation (0-2)
        """
        # Format context
        language=self.detect_language(query)
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            metadata = doc['metadata']
            source = metadata.get('url', metadata.get('filename', 'Unknown'))
            context_parts.append(f"[Context {i}]\nSource: {source}\n{doc['content']}\n")
        
        context = "\n".join(context_parts)
        
        # Create prompt based on language
        if language == 'ar':
            system_prompt = """أنت مساعد ذكي لشركة تليكوم مصر. مهمتك الإجابة على أسئلة العملاء بدقة واحترافية.

قواعد مهمة:
1. استخدم فقط المعلومات المتوفرة في السياق المقدم
2. إذا لم تجد الإجابة في السياق، قل ذلك بوضوح
3. اذكر مصدر المعلومات (الرابط أو اسم الملف)
4. كن مهذباً ومهنياً
5. أجب باللغة العربية الفصحى أو العامية حسب لغة السؤال"""

            user_prompt = f"""السياق:
{context}

السؤال: {query}

الإجابة:"""
        else:
            system_prompt = """You are an intelligent assistant for Telecom Egypt. Your task is to answer customer questions accurately and professionally.

Important rules:
1. Use ONLY the information provided in the context
2. If you cannot find the answer in the context, clearly state that
3. Cite your sources (URL or filename)
4. Be polite and professional
5. Answer in the same language as the question"""

            user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""
        
        try:
            # Call Groq API with Llama 3 70B
            start_time = time.time()
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Llama 3 70B with 8K context
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )
            
            response_time = time.time() - start_time
            response_text = chat_completion.choices[0].message.content
            
            print(f"Groq response generated in {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            print(f"Groq API error: {e}")
            error_msg = "حدث خطأ في معالجة طلبك" if language == 'ar' else "An error occurred processing your request"
            return f"{error_msg}\nError: {str(e)}"
    
    def count(self, collection_name: Optional[str] = None) -> int:
        """Count documents in collection"""
        target_collection = collection_name or self.collection_name
        try:
            collection_info = self.client.get_collection(target_collection)
            return collection_info.points_count
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0
    
    

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        collection_info = self.client.get_collection(self.collection_name)
        
        return {
            'collection_name': self.collection_name,
            'total_documents': collection_info.points_count,
            'vector_size': collection_info.config.params.vectors.size,
            'distance_metric': collection_info.config.params.vectors.distance,
            'persist_directory': self.persist_directory,
            'llm': 'Groq Llama 3 70B',
            'embedding_model': 'multilingual-e5-large'
        }
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection(collection_name=self.collection_name)
        print(f"Collection '{self.collection_name}' deleted")
    
    def reset_collection(self):
        """Reset collection (delete and recreate)"""
        try:
            self.delete_collection()
        except:
            pass
        
        self._init_collection()
        print(f"Collection '{self.collection_name}' reset")
    