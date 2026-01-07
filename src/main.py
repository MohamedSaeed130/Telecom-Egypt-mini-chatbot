from data_extraction.data_extraction_scrapy.scrapy_runner import scrapy_main
from data_extraction.data_extraction_docs.docs_processing import docs_main
from qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager
import json


docs_main(file_paths=[r"/mnt/d/AbuSamaha/test_cases/listd.pdf"],output_path="listd.json")

with open("listd.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

#print(data)
'''for page in data:
    page['chunks']=recursive_chunk(page['content'],500)
    page['chunk_length']=len(page['chunks'])

with open("test-img-4_chunked.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)'''


#data=scrapy_main(max_pages=500, base_url="https://te.eg")
#data=docs_main([r"/mnt/d/AbuSamaha/test_cases/test-img-3.png",r"/mnt/d/AbuSamaha/test_cases/test-img-4.png",r"/mnt/d/AbuSamaha/test_cases/Telecom_Egypt_Intelligent_Assistant.pdf"],output_path="docs_data.json")
