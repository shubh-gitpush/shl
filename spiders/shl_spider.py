import scrapy

class ShlSpider(scrapy.Spider):
    name = "shl"
    allowed_domains = ["shl.com"]
    start_urls = [
        "https://www.shl.com/solutions/products/product-catalog/"
    ]

    def parse(self, response):
        # Extract all links on catalog page
        links = response.css("a::attr(href)").getall()

        for link in links:
            if "/products/product-catalog/view/" in link:
                yield response.follow(link, self.parse_assessment)

    def parse_assessment(self, response):
        name = response.css("h1::text").get()
        description = " ".join(response.css("p::text").getall())

        yield {
            "name": name.strip() if name else None,
            "url": response.url,
            "description": description.strip()
        }
