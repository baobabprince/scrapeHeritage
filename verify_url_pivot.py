import asyncio
import json
from playwright.async_api import async_playwright

async def verify(url, alt_root_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        async def analyze_local_storage():
            return await page.evaluate("""() => {
                let report = [];
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    if (key && key.includes('get-tree-layout.php')) {
                        try {
                            let data = JSON.parse(localStorage.getItem(key));
                            report.push({
                                key: key.split('rootID=')[1]?.split('&')[0],
                                personCount: data.personCards ? data.personCards.length : 0,
                                rootInJSON: data.rootIndividualID
                            });
                        } catch(e) {}
                    }
                }
                return report;
            }""")

        print(f"--- Navigating to Root 1500918 ---")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        r1 = await analyze_local_storage()
        print(f"LocalStorage Entries: {json.dumps(r1, indent=2)}")

        new_url = f"https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID={alt_root_id}"
        print(f"--- Navigating to Root {alt_root_id} ---")
        await page.goto(new_url, wait_until="networkidle")
        await asyncio.sleep(5)
        r2 = await analyze_local_storage()
        print(f"LocalStorage Entries: {json.dumps(r2, indent=2)}")
        
        await browser.close()

if __name__ == "__main__":
    initial_url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
    asyncio.run(verify(initial_url, "1000352"))
