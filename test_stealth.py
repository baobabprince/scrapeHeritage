import asyncio
import time
from playwright.async_api import async_playwright

async def test_stealth_features():
    """Test stealth features work properly"""
    print("Testing stealth browser features...")
    
    async with async_playwright() as p:
        # Launch with stealth options
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        page = await context.new_page()
        
        # Test detection
        await page.goto("https://bot.sannysoft.com/")
        
        print("Waiting for detection results...")
        await asyncio.sleep(5)
        
        # Check results
        results = await page.evaluate("""
            const results = [];
            const checks = document.querySelectorAll('.main-test-item');
            checks.forEach(check => {
                const name = check.querySelector('.test-name')?.textContent;
                const status = check.querySelector('.test-status')?.textContent;
                if (name && status) {
                    results.push(`${name}: ${status}`);
                }
            });
            return results;
        """)
        
        print("\nDetection Results:")
        for result in results:
            print(f"  {result}")
        
        # Test user agent
        ua = await page.evaluate("navigator.userAgent")
        print(f"\nUser Agent: {ua}")
        
        # Test webdriver property
        webdriver = await page.evaluate("navigator.webdriver")
        print(f"Webdriver property: {webdriver}")
        
        await browser.close()
        print("\nStealth test completed!")

if __name__ == "__main__":
    asyncio.run(test_stealth_features())