import pytest
from modules.scraping import Scraper

def test_scrape_url():
    test_url = "https://raw.githubusercontent.com/ivanbicalho/python-docx-replace/refs/heads/main/README.md"
    scraper = Scraper()
    result = scraper.scrape_url(test_url)
    assert result is not None
    assert len(result) > 0
