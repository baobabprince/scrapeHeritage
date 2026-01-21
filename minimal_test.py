import asyncio
from playwright.async_api import async_playwright

async def minimal_test():
    """Test with minimal configuration like the original working version"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible to debug
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Use same URL pattern as working version
        target_url = "https://www.myheritage.co.il/family-trees/x/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
        
        print(f"Testing: {target_url}")
        
        try:
            print("Loading page...")
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            print("Waiting for content...")
            await asyncio.sleep(5)
            
            # Check page content
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Simple check - any text content?
            page_text = await page.inner_text("body")[:500]
            print(f"Page content preview: {page_text.encode('utf-8', errors='replace').decode()}")
            
            # Wait longer and check localStorage
            print("Waiting for localStorage population...")
            await asyncio.sleep(10)
            
            storage_keys = await page.evaluate("""
                let keys = [];
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    keys.push(key);
                }
                return keys;
            """)
            
            print(f"LocalStorage keys: {len(storage_keys)}")
            for key in storage_keys[:5]:  # First 5 keys
                print(f"  Key: {key}")
            
            # Try to extract data if available
            if any('get-tree-layout.php' in key for key in storage_keys):
                print("Found tree data in localStorage, attempting extraction...")
                data = await page.evaluate("""
                    (() => {
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
                    })()
                """)
                
                print(f"Extraction result: {len(data['people'])} people, {len(data['families'])} families")
            else:
                print("No tree data found in localStorage")
            
            # Keep browser open for inspection
            print("Keeping browser open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(minimal_test())