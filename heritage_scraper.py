import asyncio
import json
import os
import random
import re
import aiohttp
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

class SmartScraper:
    def __init__(self, tree_url, output_dir="output"):
        self.url = tree_url
        self.output_dir = output_dir
        self.site_id = ""
        self.tree_id = ""
        self.parse_url()
        
        # Paths
        self.base_name = f"tree_{self.site_id}"
        if self.tree_id: self.base_name += f"_{self.tree_id}"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.data_file = os.path.join(self.output_dir, f"{self.base_name}_data.json")
        self.images_dir = os.path.join(self.output_dir, f"{self.base_name}_photos")
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        # State
        self.people = {}
        self.families = {}
        self.visited_roots = set()
        self.queue = []
        
    def parse_url(self):
        """Extracts Site ID and Tree ID from URL"""
        parsed = urlparse(self.url)
        # Attempt to find Site ID in path
        # Pattern: /family-trees/Name/SITE_ID
        parts = parsed.path.split('/')
        for part in parts:
            if re.match(r'^[A-Z0-9]{10,}$', part): # Heuristic for Site Token
                self.site_id = part
                break
        
        # Extract Tree ID from query
        qs = parse_qs(parsed.query)
        self.tree_id = qs.get('familyTreeID', ['1'])[0]
        
        # Override if user provided a specific root in URL
        self.start_root = qs.get('rootIndividualID', [None])[0]

        print(f"Target: Site={self.site_id}, Tree={self.tree_id}, StartRoot={self.start_root}")

    def load_state(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p in data.get("personCards", []):
                        self.people[str(p["id"])] = p
                    for f in data.get("familyConnectors", []):
                        self.families[str(f["ID"])] = f
                print(f"Loaded {len(self.people)} existing people.")
            except Exception as e:
                print(f"Error loading state: {e}")

    def save_state(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({
                "siteId": self.site_id,
                "treeId": self.tree_id,
                "personCards": list(self.people.values()),
                "familyConnectors": list(self.families.values())
            }, f, ensure_ascii=False, indent=2)

    async def download_photo(self, session, photo_url, person_id):
        if not photo_url: return
        
        # Clean URL
        if "https://" not in photo_url: return
        
        ext = photo_url.split('.')[-1].split('/')[0]
        if len(ext) > 4: ext = "jpg"
        
        filename = f"{person_id}.{ext}"
        filepath = os.path.join(self.images_dir, filename)
        
        if os.path.exists(filepath): return # Skip existing

        try:
            async with session.get(photo_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with open(filepath, "wb") as f:
                        f.write(content)
        except Exception as e:
            # print(f"Error downloading photo for {person_id}: {e}")
            pass

    async def crawl(self):
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            page = await context.new_page()

            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
            elif len(self.people) > 0:
                self.queue = list(self.people.keys())[:100]
                random.shuffle(self.queue)
            else:
                print("No start root found and no existing data. Please provide a URL with &rootIndividualID=")
                return

            print("Starting scrape...")
            
            # Setup image downloader session
            async with aiohttp.ClientSession() as img_session:
                
                hop = 0
                consecutive_no_new = 0

                try:
                    while self.queue:
                        root_id = self.queue.pop(0)
                        
                        # Only skip if we've actively visited this node as a ROOT
                        if root_id in self.visited_roots:
                            continue
                        
                        self.visited_roots.add(root_id)
                        hop += 1
                        
                        # Construct URL
                        target_url = f"https://www.myheritage.co.il/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                        
                        print(f"[{hop}] Visiting {root_id}... (Collected: {len(self.people)})")
                        
                        try:
                            await page.goto(target_url, wait_until="domcontentloaded")
                            # Wait for API - intelligent wait
                            try:
                                await page.wait_for_selector(".person-card", timeout=5000)
                            except:
                                await asyncio.sleep(2)

                            # Extract data from localStorage
                            data = await page.evaluate("""() => {
                                let people = {};
                                let families = {};
                                for (let i = 0; i < localStorage.length; i++) {
                                    let key = localStorage.key(i);
                                    if (key && key.includes('get-tree-layout.php')) {
                                        try {
                                            let d = JSON.parse(localStorage.getItem(key));
                                            if (d.personCards) d.personCards.forEach(p => people[String(p.id)] = p);
                                            if (d.familyConnectors) d.familyConnectors.forEach(f => families[String(f.ID)] = f);
                                        } catch(e) {}
                                    }
                                }
                                return {people, families};
                            }""")

                            new_in_batch = 0
                            
                            # Process People
                            for pid, pdata in data['people'].items():
                                if pid not in self.people:
                                    self.people[pid] = pdata
                                    new_in_batch += 1
                                    
                                    # Add to queue if not visited
                                    if pid not in self.visited_roots and pid not in self.queue:
                                        self.queue.append(pid)
                                        
                                    # Download photo if exists
                                    if pdata.get('ph'):
                                        asyncio.create_task(self.download_photo(img_session, pdata['ph'], pid))

                            # Process Families
                            for fid, fdata in data['families'].items():
                                self.families[fid] = fdata
                                # Add relatives to queue
                                for rel in [fdata.get('h'), fdata.get('w')] + (fdata.get('c') or []):
                                    if rel:
                                        rid = str(rel)
                                        if rid not in self.visited_roots and rid not in self.queue:
                                            self.queue.append(rid)

                            if new_in_batch > 0:
                                print(f"    Found +{new_in_batch} new people.")
                                consecutive_no_new = 0
                            else:
                                consecutive_no_new += 1
                            
                            # Anti-ban logic: Slow down! & Shuffle
                            delay = random.uniform(8, 15) # Slower delay requested
                            if consecutive_no_new > 5:
                                print("    Stuck in known area. Shuffling queue...")
                                random.shuffle(self.queue)
                                consecutive_no_new = 0
                                delay = 2  # Fail fast if jumping
                            
                            # Save occasionally
                            if hop % 10 == 0:
                                self.save_state()
                                print(f"    Saved data. (Total: {len(self.people)})")

                            await asyncio.sleep(delay)

                        except Exception as e:
                            print(f"    Error visiting {root_id}: {e}")
                            await asyncio.sleep(5)

                except KeyboardInterrupt:
                    print("Stopping scrape...")
                finally:
                    self.save_state()
                    print(f"Done. Final count: {len(self.people)}")
                    await browser.close()

if __name__ == "__main__":
    # Example usage:
    # url = input("Enter Tree URL: ")
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
    scraper = SmartScraper(url)
    scraper.load_state()
    asyncio.run(scraper.crawl())
