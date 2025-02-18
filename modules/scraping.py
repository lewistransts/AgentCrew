import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

class Scraper:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('FC_API_KEY')
        if not api_key:
            raise ValueError("FC_API_KEY not found in environment variables")
        self.app = FirecrawlApp(api_key=api_key)

    def scrape_url(self, url: str) -> str:
        try:
            scrape_result = self.app.scrape_url(url, params={'formats': ['markdown', 'html']})
            return scrape_result.get('markdown', '')
        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")
