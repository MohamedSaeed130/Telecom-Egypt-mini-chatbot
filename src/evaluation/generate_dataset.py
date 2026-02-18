
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from ragas.testset import TestsetGenerator

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def load_documents_from_qdrant(collection_name: str = "telecom_egypt_VDB"):
    """Load documents from Qdrant collection"""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qdrant_db")

    if qdrant_url:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        client = QdrantClient(path=persist_directory)
    
    documents = []
    offset = None
    
    print("Fetching documents from Qdrant...")
    while True:
        try:
            points, offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            for point in points:
                content = point.payload.get('content', '')
                metadata = {k: v for k, v in point.payload.items() if k != 'content'}
                if content:
                    documents.append(Document(page_content=content, metadata=metadata))
            
            if offset is None:
                break
        except Exception as e:
            print(f"Error fetching documents: {e}")
            break
            
    print(f"Loaded {len(documents)} documents.")
    return documents

def generate_testset(output_file: str = "test_dataset.csv", test_size: int = 10):
    """Generate synthetic test dataset using Ragas"""
    
    # 1. Load Documents
    documents = load_documents_from_qdrant()
    if not documents:
        print("No documents found. Exiting.")
        return

    # 2. Setup LLM and Embeddings
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    generator_llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile"
    )
    
    critic_llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile"
    )

    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

    # 3. Configure Generator
    generator = TestsetGenerator.from_langchain(
        generator_llm=generator_llm,
        critic_llm=critic_llm,
        embeddings=embeddings
    )

    # 4. Generate Testset
    print(f"Generating {test_size} test questions...")
    testset = generator.generate_with_langchain_docs(
        documents,
        test_size=test_size
    )

    # 5. Save Results
    df = testset.to_pandas()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    df.to_csv(output_path, index=False)
    print(f"Testset saved to {output_path}")
    return df

if __name__ == "__main__":
    generate_testset(test_size=10)
