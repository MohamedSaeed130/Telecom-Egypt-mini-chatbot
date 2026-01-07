from typing import List, Dict, Optional
import numpy as np
from langdetect import detect
import json
import os
from ..data_chunking.text_chunker import recursive_chunk
from ..qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager

class DocumentIndexer:
    """
    Index documents from various sources into vector store
    """
    
    def __init__(self, DB_manager: QdrantVectorStoreManager):
        self.DB_manager = DB_manager
    
    def index_scraped_data(self, json_file: str):

        print(f"Loading scraped data from {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        doc_id = 0
        
        for page in data:
            # Chunk the content
            chunks = recursive_chunk(page['content'])
            
            for chunk_idx, chunk in enumerate(chunks):
                documents.append({
                    'id': f"web_{doc_id}",
                    'content': chunk,
                    'metadata': {
                        'source': 'web',
                        'url': page['url'],
                        'title': page['title'],
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks)
                    }
                })
                doc_id += 1

            try:
                self.DB_manager.add_documents(documents)
            except Exception as e:
                return f"Error adding documents: {e}"

        return documents

    
    def index_uploaded_documents(self, json_file: str):
        """Index user-uploaded documents"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []
        doc_id = self.DB_manager.collection.count()
          
        for page in data:
            chunks = recursive_chunk(page['content'])
            
            for chunk_idx, chunk in enumerate(chunks):
                documents.append({
                    'id': f"upload_{doc_id}",
                    'content': chunk,
                    'metadata': {
                        'source': 'upload',
                        'page_number':page['page_number']
                        'filename': page['filename'],
                        'file_type': page['file_type'],
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks)
                    }
                })
                doc_id += 1
        try:
            self.DB_manager.add_documents(documents)
        except Exception as e:
            return f"Error adding documents: {e}"
        return documents