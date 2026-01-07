import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse
import re
import time
from typing import Dict

class TelecomEgyptSpider(CrawlSpider):
    
    name = 'telecom_egypt'
    allowed_domains = ['te.eg', 'www.te.eg']
    start_urls =["https://te.eg"]
    
    # Custom settings for this spider
    # Note: Conflicting settings (FEEDS, CLOSESPIDER_PAGECOUNT) have been removed to allow control from scrapy_runner.py
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'DOWNLOAD_DELAY': 0.5,
        'ROBOTSTXT_OBEY': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
        },
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOAD_TIMEOUT': 30,
        'DEPTH_LIMIT': 5,
    }
    
    # Define crawling rules
    rules = (
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                deny=(
                    r'/wp-admin/',
                    r'/wp-content/',
                    r'\.pdf$',
                    r'\.zip$',
                    r'\.doc$',
                    r'\.docx$',
                ),
                unique=True
            ),
            callback='parse_page',
            follow=True
        ),
    )
    
    def __init__(self, base_url="https://te.eg", max_pages=100, *args, **kwargs):
        super(TelecomEgyptSpider, self).__init__(*args, **kwargs)
        self.max_pages = int(max_pages)
        self.pages_scraped = 0
        self.start_time = time.time()
        
        # Update start_urls and allowed_domains based on dynamic base_url
        if base_url:
            self.start_urls = [base_url]
            domain = urlparse(base_url).netloc
            if domain:
                self.allowed_domains = [domain]
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def parse_page(self, response):
        """
        Parse each page and extract content
        This is called for every page that matches the rules
        """
        
        self.pages_scraped += 1
        self.logger.info(f"Scraping page {self.pages_scraped}/{self.max_pages}: {response.url}")
        
        # Extract title
        title = response.css('title::text').get()
        if not title:
            title = response.xpath('//title/text()').get()
        
        # Extract meta description
        description = response.css('meta[name="description"]::attr(content)').get()
        if not description:
            description = response.xpath('//meta[@name="description"]/@content').get()
        
        # Extract main content - try multiple strategies
        main_content = ""
        
        # Strategy 1: Look for main content containers
        content_selectors = [
            'article::text',
            'main::text',
            'div[class*="content"]::text',
            'div[class*="main"]::text',
            'div[class*="article"]::text',
        ]
        
        for selector in content_selectors:
            content_parts = response.css(selector).getall()
            if content_parts:
                main_content += " ".join(content_parts) + " "
                break
        
        # Strategy 2: Fallback - get all text from common elements
        if not main_content.strip():
            text_elements = response.css('p::text, li::text').getall()
            main_content = " ".join(text_elements)
        
        # Extract all links on the page
        links = response.css('a::attr(href)').getall()
        absolute_links = [response.urljoin(link) for link in links if link]
        
        # Filter only te.eg domain links
        te_eg_links = [
            link for link in absolute_links 
            if urlparse(link).netloc in self.allowed_domains
        ]
        
        # Create the data item
        item = {
            'url': response.url,
            'title': self.clean_text(title or ""),
            'content': self.clean_text(main_content)
        }
        
        yield item
    
    def closed(self, reason):
        """
        Called when the spider finishes
        Print statistics
        """
        elapsed_time = time.time() - self.start_time
        
        self.logger.info("=" * 60)
        self.logger.info("Scraping Statistics:")
        self.logger.info(f"Total pages scraped: {self.pages_scraped}")
        self.logger.info(f"Time taken: {elapsed_time:.2f} seconds")
        self.logger.info(f"Average: {elapsed_time/self.pages_scraped:.2f} sec/page" if self.pages_scraped > 0 else "N/A")
        self.logger.info(f"Reason for closing: {reason}")
        self.logger.info("=" * 60)
