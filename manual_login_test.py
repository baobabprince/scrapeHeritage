import asyncio
from playwright.async_api import async_playwright

async def manual_login_test():
    """Test manual login process"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Loading login page...")
            await page.goto("https://www.myheritage.co.il/login", wait_until="networkidle", timeout=30000)
            
            print("Manually fill the form and press Enter to continue...")
            print("Email: microbiomec@gmail.com")
            print("Password: auutrnv23")
            
            # Fill automatically first
            await page.fill('input[name="registrationEmail"]', "microbiomec@gmail.com")
            await page.fill('input[name="registrationLoginPassword"]', "auutrnv23")
            
            print("Form filled. Let's wait to see what happens...")
            await asyncio.sleep(10)
            
            # Try pressing Enter
            await page.press('input[name="registrationLoginPassword"]', 'Enter')
            print("Pressed Enter on password field")
            
            print("Waiting 20 seconds to see login result...")
            await asyncio.sleep(20)
            
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            if "login" not in current_url:
                print("SUCCESS: Logged in!")
                
                # Now try accessing tree
                tree_url = "https://www.myheritage.co.il/family-trees/x/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
                await page.goto(tree_url, wait_until="networkidle", timeout=30000)
                
                print("Loading tree page...")
                await asyncio.sleep(5)
                
                # Check localStorage
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
                
                print(f"Tree data: {len(data['people'])} people, {len(data['families'])} families")
                
                if len(data['people']) > 0:
                    print("SUCCESS: Tree data accessible!")
                else:
                    print("ISSUE: No tree data found")
            else:
                print("FAILED: Still on login page")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("Keeping browser open for 60 seconds for inspection...")
            await asyncio.sleep(60)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(manual_login_test())