import scrapy
import logging

class ShlSpider(scrapy.Spider):
    name = "shl"
    allowed_domains = ["shl.com"]
    
    def __init__(self):
        # Generate paginated URLs for the product catalog
        # Based on your example: start=372 is the last page, incrementing by 12
        self.start_urls = []
        base_url = "https://www.shl.com/products/product-catalog/"
        
        # Generate URLs from start=0 to start=372, incrementing by 12
        for start in range(0, 384, 12):  # 384 to make sure we cover 372
            url = f"{base_url}?start={start}&type=1"
            self.start_urls.append(url)
        
        # Also try with type=2 parameter as in your example
        for start in range(0, 384, 12):
            url = f"{base_url}?start={start}&type=2"
            self.start_urls.append(url)
        
        self.logger.info(f"Generated {len(self.start_urls)} paginated URLs to crawl")
        super().__init__()

    def parse(self, response):
        self.logger.info(f"Parsing catalog page: {response.url}")
        
        # Check if the page loaded properly
        if response.status != 200:
            self.logger.error(f"Failed to load page: {response.url} (Status: {response.status})")
            return
        
        # Extract assessment links - try multiple selectors
        assessment_selectors = [
            "a[href*='/products/product-catalog/view/']::attr(href)",
            "a[href*='/view/']::attr(href)",
            ".product-item a::attr(href)",
            ".assessment-link::attr(href)",
            "h3 a::attr(href)",  # Many sites put assessment titles in h3 tags
            ".title a::attr(href)",
        ]
        
        assessment_links = []
        for selector in assessment_selectors:
            try:
                links = response.css(selector).getall()
                for link in links:
                    if '/view/' in link and link not in assessment_links:
                        assessment_links.append(link)
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        self.logger.info(f"Found {len(assessment_links)} assessment links on page")
        
        # Follow each assessment link
        for link in assessment_links:
            yield response.follow(link, self.parse_assessment)
        
        # If no assessment links found, log debug info
        if not assessment_links:
            self.logger.warning(f"No assessment links found on {response.url}")
            # Log some sample links for debugging
            all_links = response.css("a::attr(href)").getall()[:10]
            self.logger.debug(f"Sample links: {all_links}")
            title = response.css("title::text").get()
            self.logger.debug(f"Page title: {title}")

    def parse_assessment(self, response):
        self.logger.info(f"Parsing assessment: {response.url}")
        
        # Extract assessment data
        name = response.css("h1::text").get(default="").strip()
        if not name:
            # Try alternative selectors for name
            name = response.css(".page-title::text, .assessment-title::text, title::text").get(default="").strip()
        
        # Get description from multiple paragraph tags
        description_parts = response.css("p::text, .description::text").getall()
        description = " ".join([part.strip() for part in description_parts if part.strip()]).strip()
        
        # Get page title
        title = response.css("title::text").get(default="").strip()
        
        assessment_data = {
            "name": name,
            "url": response.url,
            "description": description,
            "title": title,
        }
        
        self.logger.info(f"Scraped assessment: {name[:50]}...")
        yield assessment_data