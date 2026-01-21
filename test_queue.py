import asyncio
import json
from stealth_scraper import StealthScraper

async def test_single_iteration():
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1000351"
    
    scraper = StealthScraper(url, output_dir="test_output")
    
    # Manually test queue building after first visit
    scraper.start_root = "1000351"
    scraper.queue = [scraper.start_root]
    
    print(f"Initial queue: {scraper.queue}")
    
    # Visit the page and see what happens
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        target_url = f"https://www.myheritage.co.il/family-trees/x/{scraper.site_id}?familyTreeID={scraper.tree_id}&rootIndividualID={scraper.start_root}"
        
        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)
        
        data = await page.evaluate("""(() => {
            let people = {};
            let families = {};
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                if (key && key.includes('get-tree-layout.php')) {
                    try {
                        let d = JSON.parse(localStorage.getItem(key));
                        if (d.personCards) d.personCards.forEach(p => people[String(p.id)] = p);
                        if (d.familyConnectors) d.familyConnectors.forEach(f => families[String(f.ID)] = f);
                    } catch(e) {}
                }
            }
            return {people, families};
        })()""")
        
        print(f"Found {len(data['people'])} people and {len(data['families'])} families")
        
        # Simulate queue building
        new_queue = []
        for pid, pdata in data['people'].items():
            if pid not in scraper.people and pid not in scraper.visited_roots:
                new_queue.append(pid)
        
        for fid, fdata in data['families'].items():
            for rel in [fdata.get('h'), fdata.get('w')] + (fdata.get('c') or []):
                if rel:
                    rid = str(rel)
                    if rid not in scraper.visited_roots and rid not in new_queue:
                        new_queue.append(rid)
        
        print(f"Queue would grow to: {len(new_queue)} items")
        print(f"New IDs: {new_queue[:10]}")  # First 10
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_single_iteration())