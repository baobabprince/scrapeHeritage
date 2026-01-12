import asyncio
import json
import os
from playwright.async_api import async_playwright

SITE_TOKEN = "OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI"
BASE_URL = f"https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/{SITE_TOKEN}?familyTreeID=1"
DATA_FILE = "full_tree_data.json"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        all_people = {}
        all_families = {}
        visited = set()
        
        # Start with fresh seed IDs
        queue = ["1500918", "1000001", "1500003", "1000124", "1000127", "1000143", "1000350", "1000507"]

        # Load existing data
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p_data in data.get("personCards", []):
                        pid = str(p_data["id"])
                        all_people[pid] = p_data
                    for f_data in data.get("familyConnectors", []):
                        all_families[str(f_data["ID"])] = f_data
                print(f"Loaded {len(all_people)} existing people.")
            except: pass

        async def extract_from_page():
            """Extract all personCards and familyConnectors from current page's localStorage"""
            return await page.evaluate("""() => {
                let people = {};
                let families = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    if (key && key.includes('get-tree-layout.php')) {
                        try {
                            let d = JSON.parse(localStorage.getItem(key));
                            if (d.personCards) {
                                d.personCards.forEach(p => {
                                    people[String(p.id)] = p;
                                });
                            }
                            if (d.familyConnectors) {
                                d.familyConnectors.forEach(f => {
                                    families[String(f.ID)] = f;
                                });
                            }
                        } catch(e) {}
                    }
                }
                return {people, families};
            }""")

        def save():
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "personCards": list(all_people.values()), 
                    "familyConnectors": list(all_families.values())
                }, f, ensure_ascii=False, indent=2)
            print(f"  Saved {len(all_people)} people to {DATA_FILE}")

        print("Starting Full Navigation Crawl...")
        
        try:
            hop = 0
            while queue and len(all_people) < 6311:
                root_id = queue.pop(0)
                if root_id in visited:
                    continue
                    
                visited.add(root_id)
                hop += 1
                
                url = f"{BASE_URL}&rootIndividualID={root_id}"
                print(f"[{hop}] Navigating to {root_id}... (Total: {len(all_people)})")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(5)  # Wait for JS to fully populate localStorage
                    
                    data = await extract_from_page()
                    
                    new_count = 0
                    for pid, pdata in data['people'].items():
                        if pid not in all_people:
                            all_people[pid] = pdata
                            new_count += 1
                            # Add new IDs to queue
                            if pid not in visited and pid not in queue:
                                queue.append(pid)
                    
                    for fid, fdata in data['families'].items():
                        all_families[fid] = fdata
                        # Add relatives from connectors
                        h = fdata.get('h')
                        w = fdata.get('w')
                        children = fdata.get('c', [])
                        for rel in [h, w] + (children or []):
                            if rel:
                                rid = str(rel)
                                if rid not in visited and rid not in queue:
                                    queue.append(rid)
                    
                    print(f"  +{new_count} new people. Queue: {len(queue)}")
                    
                    if hop % 5 == 0:
                        save()
                        
                except Exception as e:
                    print(f"  Navigation error: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            save()
            await browser.close()
            print(f"Finished. Total: {len(all_people)} people.")

if __name__ == "__main__":
    asyncio.run(run())
