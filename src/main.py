from data_extraction.data_extraction_scrapy.scrapy_runner import scrapy_main
from data_extraction.data_extraction_docs.docs_processing import docs_main
import asyncio

#data=scrapy_main(max_pages=500, base_url="https://te.eg")
data=docs_main([r"/mnt/d/AbuSamaha/test_cases/test-img-3.png",r"/mnt/d/AbuSamaha/test_cases/test-img-4.png",r"/mnt/d/AbuSamaha/test_cases/Telecom_Egypt_Intelligent_Assistant.pdf"],output_path="docs_data.json")
# src\test_cases\test-img-4.png

