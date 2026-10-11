import asyncio
import os
import re
from playwright.async_api import async_playwright

def load_config_key():
    key = os.environ.get("BROWSERLESS_API_KEY", "")
    if key and key != "YOUR_BROWSERLESS_API_KEY":
        return key

    if os.path.exists("config_secrets.txt"):
        try:
            with open("config_secrets.txt", "r", encoding="utf-8") as f:
                for line in f:
                    match = re.match(r'^\s*BROWSERLESS_API_KEY\s*=\s*["\']?([^"\']+)["\']?', line)
                    if match:
                        val = match.group(1).strip()
                        if val and val != "YOUR_BROWSERLESS_API_KEY":
                            return val
        except Exception:
            pass
    return ""

async def test_browserless():
    api_key = load_config_key()
    if not api_key:
        print("BROWSERLESS_API_KEY is not set!")
        return

    # Browserless endpoint URL
    # Can use connect_over_cdp with wss://chrome.browserless.io?token=KEY
    # or wss://chrome.browserless.io/playwright?token=KEY
    ws_endpoint = f"wss://chrome.browserless.io?token={api_key}"
    print(f"Connecting to Browserless: wss://chrome.browserless.io?token={api_key[:6]}...")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            print("Successfully connected to Browserless via CDP!")

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
            )

            page = await context.new_page()
            print("Navigating to https://www.myheritage.co.il/login...")
            await page.goto("https://www.myheritage.co.il/login", wait_until="networkidle", timeout=30000)

            title = await page.title()
            print(f"Page title: {title}")
            print(f"Page URL: {page.url}")

            # Check login inputs presence
            email_field = await page.query_selector('input[type="email"], input[name="registrationEmail"]')
            if email_field:
                print("Email field found on login page!")
            else:
                print("Email field NOT found!")

            await browser.close()
            print("Browserless test completed successfully!")

        except Exception as e:
            print(f"Error testing Browserless: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browserless())
