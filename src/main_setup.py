
from sympy.polys.polyconfig import query
from data_extraction.data_extraction_scrapy.scrapy_runner import TelecomEgyptScraper
from data_extraction.data_extraction_docs.docs_processing import TelecomEgyptDocumentProcessor
from data_chunking.text_chunker import recursive_chunk
from data_indexer.data_indexing import DocumentIndexer
from qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager
import os
import json
from typing import List



def web_scraping(max_pages: int=200, base_url: str=None,output_file_name: str=None):
    # Create and run scraper
    if not os.path.exists(output_file_name):
        scraper=TelecomEgyptScraper(max_pages=max_pages, base_url=base_url, output_file=output_file_name)
        data=scraper.crawl()
        if data is None:
            return False
        return True
    
    return "existed"
  
    

def upload_docs_processing(file_paths: List[str], output_path: str):
    # Process documents
    processor = TelecomEgyptDocumentProcessor()
    processor.process_multiple_documents(file_paths, output_path)
    return 

def setup():
    qdrant_DB = QdrantVectorStoreManager(
    groq_api_key="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",
    collection_name="telecom_egypt_VDB",
    persist_directory="qdrant_db",
    embedding_model_name="intfloat/multilingual-e5-large",
    use_cloud=True,
    qdrant_url="https://69176c33-c757-41a8-ab60-d18bfca81717.europe-west3-0.gcp.cloud.qdrant.io",
    qdrant_api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.g6gizwnNagX1qf8pTgca4xsfDFQm8W5dT-gsbEjd0fM"
    )

    indexer=DocumentIndexer(qdrant_DB)

    web_scraping(max_pages=500, base_url="https://te.eg",output_file_name="telecom_egypt_web_scraping.json")
    _=indexer.index_scraped_data("telecom_egypt_web_scraping.json",chunk_size=512, overlap=128, batch_size=256)
    stats=qdrant_DB.get_collection_stats()
    print(stats)
    
    return 


if __name__ == "__main__":
    setup()
   