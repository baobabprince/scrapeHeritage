import asyncio
from playwright.async_api import async_playwright

async def basic_test():
    """Simple test to see if page loads at all"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        # Test the original working URL
        url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
        
        print(f"Testing: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page loaded successfully")
            
            # Check if page contains family tree content
            title = await page.title()
            print(f"Page title: {title.encode('utf-8', errors='replace').decode()}")
            
            # Look for any family tree elements
            person_cards = await page.query_selector_all(".person-card")
            print(f"Person cards found: {len(person_cards)}")
            
            # Check localStorage size
            storage_size = await page.evaluate("localStorage.length")
            print(f"LocalStorage keys: {storage_size}")
            
            # Wait longer and check again
            await asyncio.sleep(10)
            
            data = await page.evaluate("""
                (() => {
                    let people = {};
                    let families = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        console.log('Key:', key);
                        if (key && key.includes('get-tree-layout.php')) {
                            try {
                                let d = JSON.parse(localStorage.getItem(key));
                                if (d.personCards) d.personCards.forEach(p => people[String(p.id)] = p);
                                if (d.familyConnectors) d.familyConnectors.forEach(f => families[String(f.ID)] = f);
                            } catch(e) {}
                        }
                    }
                    return {people, families};
                })()
            """)
            
            print(f"After waiting: {len(data['people'])} people, {len(data['families'])} families")
            
            await asyncio.sleep(30)  # Keep browser open for 30 seconds
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(basic_test())