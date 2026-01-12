import asyncio
import json
import os
from playwright.async_api import async_playwright

SITE_TOKEN = "OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI"
DATA_FILE = "full_tree_data.json"
STATE_FILE = "crawler_state.json"

# API URL template found in localStorage
API_BASE = "/FP/API/FamilyTree/get-tree-layout.php"
API_PARAMS = f"clientVersion=3073&s={SITE_TOKEN}&familyTreeID=1&familyTreeRev=1767518812&smartMatchesRev=0&recordMatchesRev=0&clientDate=2026-01-12&rmFilter=&lang=HE&dataLang=DF&treeStyle=1&memberID=OYYV6A7R64CDRYWOIOI3YM4FSQEBPCY&addMeCards=0&classic=0&maxProximityLevel=7&maxIndividualsAfterPrune=1000&shouldFetchCousins=0&shouldFetchDnaInfo=0&shouldFetchSMInfo=0&shouldFetchRMInfo=0&isFlatLook=0&isFaceLift=1&pap=0&colorCodes=1"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        all_people = {}
        all_families = {}
        visited = set()
        queue = ["1500918", "1000001", "1500003"]

        # Load existing data
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
                    queue = state.get("queue", queue)
                    visited = set(state.get("pivoted_roots", []))
            except: pass

        # First, navigate to the site to establish cookies
        print("Establishing session...")
        await page.goto(f"https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/{SITE_TOKEN}?familyTreeID=1&rootIndividualID=1500918", timeout=60000)
        await asyncio.sleep(8)

        async def fetch_neighborhood(root_id):
            """Fetch tree data for a specific root using in-page fetch"""
            js_code = f"""
                (async () => {{
                    const url = "{API_BASE}?{API_PARAMS}&rootID={root_id}";
                    try {{
                        const resp = await fetch(url);
                        const data = await resp.json();
                        return data;
                    }} catch(e) {{
                        return {{error: e.message}};
                    }}
                }})()
            """
            return await page.evaluate(js_code)

        def save():
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"personCards": list(all_people.values()), "familyConnectors": list(all_families.values())}, f, ensure_ascii=False, indent=2)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"queue": list(set(queue) - visited), "pivoted_roots": list(visited)}, f, ensure_ascii=False, indent=2)

        print(f"Starting API Crawl. Loaded {len(all_people)} people.")
        
        try:
            hop = 0
            while queue and len(all_people) < 6311:
                root_id = queue.pop(0)
                if root_id in visited:
                    continue
                
                visited.add(root_id)
                hop += 1
                
                print(f"[{hop}] Fetching root {root_id}... People: {len(all_people)}")
                
                data = await fetch_neighborhood(root_id)
                
                if data and not data.get("error"):
                    new_count = 0
                    if data.get("personCards"):
                        for pc in data["personCards"]:
                            pid = str(pc["id"])
                            if pid not in all_people:
                                all_people[pid] = pc
                                new_count += 1
                                if pid not in visited and pid not in queue:
                                    queue.append(pid)
                    
                    if data.get("familyConnectors"):
                        for fc in data["familyConnectors"]:
                            fid = str(fc["ID"])
                            all_families[fid] = fc
                            # Add relatives
                            for rel in [fc.get("h"), fc.get("w")] + (fc.get("c") or []):
                                if rel:
                                    rid = str(rel)
                                    if rid not in visited and rid not in queue:
                                        queue.append(rid)
                    
                    print(f"    +{new_count} new. Queue: {len(queue)}")
                else:
                    print(f"    Error: {data.get('error', 'Unknown')}")
                
                if hop % 10 == 0:
                    save()
                    print("    Progress saved.")
                
                await asyncio.sleep(1.5)  # Rate limiting
                
        except KeyboardInterrupt:
            print("Interrupted.")
        finally:
            save()
            await browser.close()
            print(f"Final: {len(all_people)} people")

if __name__ == "__main__":
    asyncio.run(run())
