import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
import os
from typing import Dict, List
from .scrapy_spider import TelecomEgyptSpider


class TelecomEgyptScraper:
    
    def __init__(self, base_url: str = "https://te.eg", max_pages: int = 100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.output_file = "telecom_egypt_data.json"
    
    def crawl(self) -> List[Dict]:
        """
        Run the Scrapy spider
        """
        # Configure Scrapy settings
        settings = {
            'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            },
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 5,
            'DOWNLOAD_DELAY': 0.5,
            'COOKIES_ENABLED': False,
            'RETRY_TIMES': 3,
            'DOWNLOAD_TIMEOUT': 30,
            'DEPTH_LIMIT': 3,
            'CLOSESPIDER_PAGECOUNT': self.max_pages,
            
            # Output to JSON
            'FEEDS': {
                self.output_file: {
                    'format': 'json',
                    'encoding': 'utf8',
                    'indent': 2,
                    'ensure_ascii': False,
                    'overwrite': True,
                }
            },
            
            # Logging
            'LOG_LEVEL': 'INFO',
            'LOG_FORMAT': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            
            # Caching
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_EXPIRATION_SECS': 86400,
            'HTTPCACHE_DIR': 'httpcache',
            
            # AutoThrottle
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 0.5,
            'AUTOTHROTTLE_MAX_DELAY': 3,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 5.0,
        }
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Start crawling
        print(f"Starting Scrapy crawler for {self.base_url}...")
        print(f"Maximum pages: {self.max_pages}")
        print("=" * 60)
        
        process.crawl(
            TelecomEgyptSpider,
            max_pages=self.max_pages,
            start_urls=[self.base_url]
        )
        
        # Run the crawler (blocking)
        process.start()
        
        # Load and return results
        return self.load_results()
    
    def load_results(self) -> List[Dict]:
        """Load scraped results from JSON file"""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_to_json(self, filename: str = None):

        if filename and filename != self.output_file:
            data = self.load_results()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data copied to {filename}")
        else:
            print(f"Data already saved to {self.output_file}")
    
    def get_statistics(self) -> Dict:
        """Get scraping statistics"""
        data = self.load_results()
        
        if not data:
            return {
                'total_pages': 0,
                'total_urls_visited': 0,
                'total_content_length': 0,
                'avg_content_length': 0
            }
        
        total_content_length = sum(len(page.get('content', '')) for page in data)
        
        # Count unique URLs
        all_links = set()
        for page in data:
            all_links.update(page.get('links', []))
            all_links.add(page.get('url'))
        
        return {
            'total_pages': len(data),
            'total_urls_visited': len(all_links),
            'total_content_length': total_content_length,
            'avg_content_length': total_content_length / len(data) if data else 0
        }


def scrapy_main(max_pages: int = 100, base_url: str = "https://te.eg"):
    """
    Main function for direct execution
    Compatible with original interface
    """
    # Create and run scraper
    scraper = TelecomEgyptScraper(max_pages=max_pages, base_url=base_url)
    data = scraper.crawl()
    
    # Print statistics
    stats = scraper.get_statistics()
    print("\n" + "=" * 60)
    print("Scraping Statistics:")
    print(json.dumps(stats, indent=2))
    print("=" * 60)
    
    return data
