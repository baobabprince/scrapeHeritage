import asyncio
import json
from playwright.async_api import async_playwright

async def run(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        graphql_calls = []
        async def handle_request(request):
            if "graphql" in request.url:
                try:
                    pld = request.post_data
                    graphql_calls.append({"url": request.url, "payload": pld})
                except:
                    pass

        page.on("request", handle_request)
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        with open("graphql_calls.json", "w", encoding="utf-8") as f:
            json.dump(graphql_calls, f, ensure_ascii=False, indent=2)
            
        print("Done. Check graphql_calls.json")
        await browser.close()

if __name__ == "__main__":
    target_url = "https://www.myheritage.com/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
    asyncio.run(run(target_url))
