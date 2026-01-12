import asyncio
import json
import os
import random
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

        # Load existing data
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p_data in data.get("personCards", []):
                        pid = str(p_data["id"])
                        all_people[pid] = p_data
                        # Don't mark as visited - we want to pivot to them to discover more
                    for f_data in data.get("familyConnectors", []):
                        all_families[str(f_data["ID"])] = f_data
                print(f"Loaded {len(all_people)} existing people.")
            except: pass

        # Build queue from existing data - prioritize IDs we haven't pivoted to yet
        # Start with a mix of prefixes
        all_ids = list(all_people.keys())
        random.shuffle(all_ids)
        queue = all_ids[:100]  # Start with 100 random seeds from our data

        async def extract_from_page():
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

        print(f"Starting Diverse Crawl... Queue: {len(queue)}")
        
        try:
            hop = 0
            no_new_streak = 0
            
            while queue and len(all_people) < 6311:
                root_id = queue.pop(0)
                if root_id in visited:
                    continue
                    
                visited.add(root_id)
                hop += 1
                
                url = f"{BASE_URL}&rootIndividualID={root_id}"
                print(f"[{hop}] -> {root_id} (Total: {len(all_people)}, Queue: {len(queue)})")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(4)
                    
                    data = await extract_from_page()
                    
                    new_count = 0
                    for pid, pdata in data['people'].items():
                        if pid not in all_people:
                            all_people[pid] = pdata
                            new_count += 1
                            if pid not in visited and pid not in queue:
                                queue.append(pid)
                    
                    for fid, fdata in data['families'].items():
                        all_families[fid] = fdata
                        for rel in [fdata.get('h'), fdata.get('w')] + (fdata.get('c') or []):
                            if rel:
                                rid = str(rel)
                                if rid not in visited and rid not in queue:
                                    queue.append(rid)
                    
                    if new_count > 0:
                        print(f"    +{new_count} new!")
                        no_new_streak = 0
                    else:
                        no_new_streak += 1
                    
                    # If we're stuck, shuffle the queue
                    if no_new_streak > 20:
                        random.shuffle(queue)
                        no_new_streak = 0
                        print("    Shuffled queue to explore new areas.")
                    
                    if hop % 10 == 0:
                        save()
                        print(f"    Saved. Total: {len(all_people)}")
                        
                except Exception as e:
                    print(f"    Error: {e}")
                    await asyncio.sleep(3)
                    
        except KeyboardInterrupt:
            print("Interrupted.")
        finally:
            save()
            await browser.close()
            print(f"Final: {len(all_people)} people.")

if __name__ == "__main__":
    asyncio.run(run())
