import asyncio
import json
from stealth_scraper import StealthScraper

def fresh_test():
    # Start fresh without loading any existing data
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1000351"
    
    scraper = StealthScraper(url, output_dir="fresh_test")
    # CRITICAL: Don't call load_state()!
    
    print("Starting fresh scrape without existing data...")
    asyncio.run(scraper.crawl())

if __name__ == "__main__":
    fresh_test()