import asyncio
import json
import os
import random
import time
from typing import List, Dict
from playwright.async_api import async_playwright, BrowserContext, Page

class StealthScraper:
    def __init__(self, tree_url: str, output_dir: str = "output"):
        self.url = tree_url
        self.output_dir = output_dir
        self.site_id = ""
        self.tree_id = ""
        self.parse_url()
        
        # Paths
        self.base_name = f"tree_{self.site_id}"
        if self.tree_id: 
            self.base_name += f"_{self.tree_id}"
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.data_file = os.path.join(self.output_dir, f"{self.base_name}_data.json")
        
        # State
        self.people = {}
        self.families = {}
        self.visited_roots = set()
        self.queue = []
        
        # Anti-detection settings
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0"
        ]
        
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720}
        ]
        
        self.request_count = 0
        self.last_request_time = 0

    def parse_url(self):
        """Extracts Site ID and Tree ID from URL"""
        from urllib.parse import urlparse, parse_qs
        import re
        
        parsed = urlparse(self.url)
        parts = parsed.path.split('/')
        for part in parts:
            if re.match(r'^[A-Z0-9]{10,}$', part):
                self.site_id = part
                break
        
        qs = parse_qs(parsed.query)
        self.tree_id = qs.get('familyTreeID', ['1'])[0]
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

    def get_random_delay(self, min_delay: float = 5, max_delay: float = 25) -> float:
        """Generate human-like random delay with occasional longer pauses"""
        base_delay = random.uniform(min_delay, max_delay)
        
        # Occasionally take longer breaks (simulating user distraction)
        if random.random() < 0.1:  # 10% chance
            base_delay += random.uniform(30, 90)
        
        # Add small random variation
        base_delay += random.uniform(-1, 1)
        
        return max(min_delay, base_delay)

    async def create_stealth_context(self, playwright) -> BrowserContext:
        """Create browser context with anti-detection measures"""
        user_agent = random.choice(self.user_agents)
        viewport = random.choice(self.viewports)
        
        # Random browser language
        languages = ['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'he-IL,he;q=0.9,en;q=0.8']
        
        context = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Speed up scraping
                # JavaScript enabled - needed for data loading
            ]
        )
        
        browser_context = await context.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': random.choice(languages),
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        
        # Add stealth scripts to hide automation
        await browser_context.add_init_script("""
            // Remove webdriver traces
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Hide automation in Chrome
            window.chrome = {
                runtime: {},
            };
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        return browser_context

    async def simulate_human_behavior(self, page: Page):
        """Simulate human-like interactions"""
        # Random mouse movements
        await page.mouse.move(
            random.randint(100, 800),
            random.randint(100, 600)
        )
        
        # Occasionally scroll
        if random.random() < 0.3:  # 30% chance
            await page.mouse.wheel(0, random.randint(-200, 200))
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Random click (not on actual elements)
        if random.random() < 0.1:  # 10% chance
            await page.mouse.click(
                random.randint(100, 800),
                random.randint(100, 600)
            )

    async def rate_limit_request(self):
        """Implement intelligent rate limiting"""
        current_time = time.time()
        
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            
            # Minimum delay between requests
            min_delay = 2.0
            if time_since_last < min_delay:
                await asyncio.sleep(min_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Every 50 requests, take a longer break
        if self.request_count % 50 == 0:
            break_duration = random.uniform(60, 180)
            print(f"Taking a {break_duration:.0f}s break after {self.request_count} requests...")
            await asyncio.sleep(break_duration)

    async def crawl(self):
        async with async_playwright() as p:
            print("Launching stealth browser...")
            context = await self.create_stealth_context(p)
            page = await context.new_page()
            
            # Enable JavaScript selectively for this site
            await page.context.set_extra_http_headers({
                'Content-Security-Policy': 'script-src *'
            })
            
            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
            elif len(self.people) > 0:
                self.queue = list(self.people.keys())[:100]
                random.shuffle(self.queue)
            else:
                print("No start root found. Please provide a URL with &rootIndividualID=")
                return

            print("Starting stealth scrape...")
            
            hop = 0
            consecutive_no_new = 0

            try:
                while self.queue:
                    root_id = self.queue.pop(0)
                    
                    if root_id in self.visited_roots:
                        continue
                    
                    self.visited_roots.add(root_id)
                    hop += 1
                    
                    # Rate limiting
                    await self.rate_limit_request()
                    
                    # Construct URL
                    target_url = f"https://www.myheritage.co.il/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                    
                    print(f"[{hop}] Visiting {root_id}... (Collected: {len(self.people)})")
                    
                    try:
                        # Simulate human behavior before navigation
                        await self.simulate_human_behavior(page)
                        
                        await page.goto(target_url, wait_until="networkidle", timeout=90000)
                        
                        # Wait for content with random delay
                        try:
                            await page.wait_for_selector(".person-card", timeout=8000)
                        except:
                            await asyncio.sleep(random.uniform(2, 4))

                        # Simulate human behavior after page load
                        await self.simulate_human_behavior(page)

                        # Extract data from localStorage
                        data = await page.evaluate("""(() => {
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
                        })()""")

                        print(f"    DEBUG: Found {len(data['people'])} people, {len(data['families'])} families in localStorage")
                        
                        new_in_batch = 0
                        
                        # Process People
                        for pid, pdata in data['people'].items():
                            if pid not in self.people:
                                self.people[pid] = pdata
                                new_in_batch += 1
                                print(f"    Added person {pid}: {pdata.get('fn', 'Unknown')} {pdata.get('ln', '')}")
                                
                                if pid not in self.visited_roots and pid not in self.queue:
                                    self.queue.append(pid)

                        # Process Families
                        for fid, fdata in data['families'].items():
                            self.families[fid] = fdata
                            for rel in [fdata.get('h'), fdata.get('w')] + (fdata.get('c') or []):
                                if rel:
                                    rid = str(rel)
                                    if rid not in self.visited_roots and rid not in self.queue:
                                        self.queue.append(rid)

                        if new_in_batch > 0:
                            print(f"    Found +{new_in_batch} new people. Queue: {len(self.queue)} items")
                            consecutive_no_new = 0
                        else:
                            consecutive_no_new += 1
                            print(f"    No new people. Queue: {len(self.queue)} items")
                        
                        # Anti-detection: Variable delays and queue shuffling
                        delay = self.get_random_delay()
                        
                        if consecutive_no_new > 5:
                            print("    Stuck in known area. Shuffling queue...")
                            random.shuffle(self.queue)
                            consecutive_no_new = 0
                            delay = random.uniform(10, 20)
                        
                        # Save periodically
                        if hop % 15 == 0:
                            self.save_state()
                            print(f"    Saved data. (Total: {len(self.people)})")

                        await asyncio.sleep(delay)

                    except Exception as e:
                        print(f"    Error visiting {root_id}: {e}")
                        await asyncio.sleep(random.uniform(5, 10))

            except KeyboardInterrupt:
                print("Stopping scrape...")
            finally:
                self.save_state()
                print(f"Done. Final count: {len(self.people)} people collected.")
                await context.close()

if __name__ == "__main__":
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1000351"
    scraper = StealthScraper(url, output_dir="fresh_output")
    # Don't load existing data to test fresh discovery
    # scraper.load_state()
    asyncio.run(scraper.crawl())