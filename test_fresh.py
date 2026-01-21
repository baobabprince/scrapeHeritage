import asyncio
import json
from stealth_scraper import StealthScraper

def test_with_different_start():
    # Try starting from a different person ID
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1000351"
    
    scraper = StealthScraper(url, output_dir="test_output")
    # Don't load existing data to force fresh discovery
    asyncio.run(scraper.crawl())

if __name__ == "__main__":
    test_with_different_start()