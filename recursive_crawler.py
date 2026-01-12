import asyncio
import json
import os
import random
from playwright.async_api import async_playwright

# Configuration
SITE_TOKEN = "OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI"
BASE_URL = f"https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/{SITE_TOKEN}?familyTreeID=1"
DATA_FILE = "full_tree_data.json"
STATE_FILE = "crawler_state.json"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        all_people = {}
        all_families = {}
        pivoted_roots = set()
        queue = []

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p_data in data.get("personCards", []):
                        all_people[str(p_data["id"])] = p_data
                    for f_data in data.get("familyConnectors", []):
                        all_families[str(f_data["ID"])] = f_data
            except: pass

        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    queue = state.get("queue", [])
                    pivoted_roots = set(state.get("pivoted_roots", []))
            except: pass

        async def extract_neighborhood():
            return await page.evaluate("""() => {
                let people = {};
                let families = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    if (key && key.includes('get-tree-layout.php')) {
                        try {
                            let d = JSON.parse(localStorage.getItem(key));
                            if (d.personCards) d.personCards.forEach(p => people[p.id] = p);
                            if (d.familyConnectors) d.familyConnectors.forEach(f => families[f.ID] = f);
                        } catch(e) {}
                    }
                }
                return {people, families};
            }""")

        def save():
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"personCards": list(all_people.values()), "familyConnectors": list(all_families.values())}, f, ensure_ascii=False, indent=2)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                clean_queue = [qid for qid in list(dict.fromkeys(queue)) if qid not in pivoted_roots]
                json.dump({"queue": clean_queue, "pivoted_roots": list(pivoted_roots)}, f, ensure_ascii=False, indent=2)

        print(f"Starting Leaf-Expanding Crawl... (Restored {len(all_people)})")
        
        try:
            while (queue or len(all_people) < 6311):
                if not queue:
                    # If queue empty, find people with least relatives or "furthest" in coordinates
                    print("Queue empty. Finding new bridgeheads from existing data...")
                    potential = [pid for pid in all_people.keys() if pid not in pivoted_roots]
                    if not potential: break
                    queue = random.sample(potential, min(len(potential), 50))
                
                curr_id = queue.pop(0)
                if curr_id in pivoted_roots: continue
                
                print(f"Pivoting to: {curr_id}... Total: {len(all_people)}")
                pivoted_roots.add(curr_id)
                
                try:
                    await page.goto(f"{BASE_URL}&rootIndividualID={curr_id}", wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(5) 
                    
                    data = await extract_neighborhood()
                    new_count = 0
                    for pid, p_data in data['people'].items():
                        pid_str = str(pid)
                        if pid_str not in all_people:
                            all_people[pid_str] = p_data
                            new_count += 1
                    
                    for fid, f_data in data['families'].items():
                        all_families[str(fid)] = f_data
                        relatives = [str(f_data.get('h')), str(f_data.get('w'))] + [str(c) for c in f_data.get('c', [])]
                        for rid in relatives:
                            if rid != 'None' and rid not in pivoted_roots and rid not in queue:
                                queue.append(rid)
                    
                    print(f"  + {new_count} people. Queue: {len(queue)}")
                    if len(pivoted_roots) % 10 == 0: save()
                        
                except Exception as e:
                    print(f"  Error: {e}")
                    await asyncio.sleep(5)

        finally:
            save()
            await browser.close()
            print(f"Final Count: {len(all_people)}")

if __name__ == "__main__":
    asyncio.run(run())
