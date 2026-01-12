import asyncio
import json
import random
from playwright.async_api import async_playwright

async def harvest():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except:
            print("Initial navigation timeout. Proceeding...")

        # Screenshot for debug
        await page.screenshot(path="search_init_debug.png")
        
        # Handle cookie banner
        try:
            cookie_btn = page.locator("button:has-text('מסכים'), button:has-text('Agree'), #root-set-cookie-accept")
            if await cookie_btn.count() > 0:
                await cookie_btn.first.click()
                print("Clicked cookie banner.")
        except:
            pass

        await asyncio.sleep(5)
        
        # Wait for tree or search box
        try:
            await page.wait_for_selector("input#FindAPerson, .search_input, #pedigree_tree_find_person", timeout=30000)
            print("Found search box.")
        except:
            print("Search box not found. Saving debug screenshot.")
            await page.screenshot(path="search_box_not_found.png")
            await browser.close()
            return

        search_input = page.locator("input#FindAPerson, #pedigree_tree_find_person").first
        
        found_ids = set()
        alphabet = "אבגדהוזחטיכלמנסעפצקרשת"
        
        for char in alphabet:
            print(f"Searching for '{char}'...")
            try:
                await search_input.click()
                await search_input.fill("")
                await search_input.type(char, delay=150)
                await asyncio.sleep(4) 
                
                # Capture all links in the entire page that match person- pattern
                links = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => a.href)
                        .filter(href => href.includes('person-'));
                }""")
                
                new_extracted = 0
                for href in links:
                    try:
                        if 'person-' in href:
                            # Extract ID: person-ID_1_1
                            pid = href.split('person-')[1].split('_')[0]
                            if pid not in found_ids:
                                found_ids.add(pid)
                                new_extracted += 1
                    except:
                        pass
                
                print(f"  Extracted {new_extracted} new IDs. Total: {len(found_ids)}")
                
            except Exception as e:
                print(f"  Error searching for '{char}': {e}")
                
            await asyncio.sleep(random.random() * 2)

        print(f"Finished. Total IDs: {len(found_ids)}")
        with open("harvested_ids.json", "w", encoding="utf-8") as f:
            json.dump(list(found_ids), f, ensure_ascii=False, indent=2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(harvest())
