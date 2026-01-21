import asyncio
from playwright.async_api import async_playwright

async def debug_login_page():
    """Debug MyHeritage login page to find correct selectors"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Loading login page...")
            await page.goto("https://www.myheritage.co.il/login", wait_until="networkidle", timeout=30000)
            
            print("Page loaded. Analyzing form elements...")
            
            # Find all input fields
            inputs = await page.query_selector_all("input")
            print(f"Found {len(inputs)} input fields:")
            
            for i, input_el in enumerate(inputs):
                input_type = await input_el.get_attribute("type")
                input_name = await input_el.get_attribute("name")
                input_id = await input_el.get_attribute("id")
                input_placeholder = await input_el.get_attribute("placeholder")
                
                print(f"  Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            
            # Find all buttons
            buttons = await page.query_selector_all("button, input[type='submit']")
            print(f"\nFound {len(buttons)} buttons:")
            
            for i, button in enumerate(buttons):
                button_text = await button.inner_text()
                button_type = await button.get_attribute("type")
                button_class = await button.get_attribute("class")
                
                try:
                    print(f"  Button {i+1}: text='{button_text}', type='{button_type}', class='{button_class}'")
                except:
                    print(f"  Button {i+1}: text='(encoding error)', type='{button_type}', class='{button_class}'")
            
            # Take screenshot for manual inspection
            await page.screenshot(path="login_page_debug.png")
            print("\nScreenshot saved as 'login_page_debug.png'")
            
            print("\nWaiting 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login_page())