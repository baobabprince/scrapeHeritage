import asyncio
import json
import os
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, ProxySettings

class ProxyRotator:
    def __init__(self):
        self.proxies = [
            # Add your proxy list here
            # Format: {'server': 'http://proxy:port', 'username': 'user', 'password': 'pass'}
            # For free proxies, use without auth
        ]
        self.current_index = 0
        
    def get_next_proxy(self) -> Optional[ProxySettings]:
        if not self.proxies:
            return None
            
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        if 'username' in proxy and 'password' in proxy:
            return ProxySettings(
                server=proxy['server'],
                username=proxy['username'],
                password=proxy['password']
            )
        else:
            return ProxySettings(server=proxy['server'])
    
    def add_proxy(self, server: str, username: str = None, password: str = None):
        proxy = {'server': server}
        if username and password:
            proxy['username'] = username
            proxy['password'] = password
        self.proxies.append(proxy)

class AdvancedStealthScraper:
    def __init__(self, tree_url: str, output_dir: str = "output", use_proxy: bool = False):
        self.url = tree_url
        self.output_dir = output_dir
        self.use_proxy = use_proxy
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
        
        # Proxy rotator
        self.proxy_rotator = ProxyRotator()
        
        # Enhanced anti-detection settings
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"
        ]
        
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720},
            {'width': 1600, 'height': 900}
        ]
        
        self.request_count = 0
        self.last_request_time = 0
        self.session_start_time = 0

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

    def get_realistic_delay(self) -> float:
        """Generate realistic human-like delays"""
        # Base delay with normal distribution
        base_delay = random.gauss(12, 4)  # Mean 12s, std dev 4s
        base_delay = max(5, min(25, base_delay))  # Clamp between 5-25s
        
        # Time-based patterns
        current_hour = time.localtime().tm_hour
        
        # Slower during business hours (9-17)
        if 9 <= current_hour <= 17:
            base_delay *= 1.3
        # Faster late at night (23-6)
        elif current_hour >= 23 or current_hour <= 6:
            base_delay *= 0.8
        
        # Occasional long breaks (simulating user getting distracted)
        if random.random() < 0.08:  # 8% chance
            base_delay += random.uniform(60, 180)
        
        # Session fatigue - longer delays as session progresses
        session_duration = time.time() - self.session_start_time
        if session_duration > 1800:  # After 30 minutes
            base_delay *= (1 + session_duration / 7200)  # Gradual increase
        
        return base_delay

    async def create_advanced_stealth_context(self, playwright) -> BrowserContext:
        """Create browser context with advanced anti-detection"""
        user_agent = random.choice(self.user_agents)
        viewport = random.choice(self.viewports)
        
        # Random browser settings
        languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9', 
            'he-IL,he;q=0.9,en;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8'
        ]
        
        # Get proxy if enabled
        proxy = self.proxy_rotator.get_next_proxy() if self.use_proxy else None
        
        context = await playwright.chromium.launch(
            headless=True,
            proxy=proxy,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-background-timer-throttling',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-logging',
                '--disable-gpu-logging',
                '--silent',
                '--log-level=3'
            ]
        )
        
        browser_context = await context.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale=random.choice(['en-US', 'en-GB', 'he-IL']),
            timezone_id=random.choice(['America/New_York', 'Europe/London', 'Asia/Jerusalem']),
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': random.choice(languages),
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            },
            permissions=['geolocation']
        )
        
        # Advanced stealth scripts
        await browser_context.add_init_script("""
            // Remove webdriver traces completely
            delete navigator.__proto__.webdriver;
            
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }
                ],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            
            // Override permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock Chrome runtime
            window.chrome = {
                runtime: {
                    onConnect: undefined,
                    onMessage: undefined
                },
                app: {
                    isInstalled: false
                }
            };
            
            // Override WebGL parameters
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) HD Graphics 630';
                }
                return getParameter(parameter);
            };
            
            // Randomize canvas fingerprint
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 2 - 1;
                        imageData.data[i + 1] += Math.random() * 2 - 1;
                        imageData.data[i + 2] += Math.random() * 2 - 1;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, args);
            };
        """)
        
        return browser_context

    async def simulate_advanced_human_behavior(self, page: Page):
        """Simulate complex human-like interactions"""
        # Random mouse movements with curves
        for _ in range(random.randint(1, 3)):
            start_x = random.randint(100, 800)
            start_y = random.randint(100, 600)
            end_x = random.randint(100, 800)
            end_y = random.randint(100, 600)
            
            # Bezier curve movement
            steps = random.randint(5, 15)
            for i in range(steps):
                t = i / steps
                # Quadratic bezier curve
                x = (1-t)*(1-t)*start_x + 2*(1-t)*t*random.randint(100, 800) + t*t*end_x
                y = (1-t)*(1-t)*start_y + 2*(1-t)*t*random.randint(100, 600) + t*t*end_y
                
                await page.mouse.move(int(x), int(y))
                await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # Natural scrolling patterns
        if random.random() < 0.4:  # 40% chance
            scroll_direction = random.choice(['down', 'up'])
            scroll_amount = random.randint(100, 500)
            
            if scroll_direction == 'down':
                await page.mouse.wheel(0, scroll_amount)
            else:
                await page.mouse.wheel(0, -scroll_amount)
            
            await asyncio.sleep(random.uniform(0.5, 2))
        
        # Occasional keyboard interaction
        if random.random() < 0.15:  # 15% chance
            await page.keyboard.press('Tab')
            await asyncio.sleep(random.uniform(0.2, 0.8))

    async def intelligent_rate_limit(self):
        """Advanced rate limiting with adaptive timing"""
        current_time = time.time()
        
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            
            # Adaptive minimum delay based on time of day
            current_hour = time.localtime().tm_hour
            if 9 <= current_hour <= 17:  # Business hours
                min_delay = 3.0
            elif 18 <= current_hour <= 22:  # Evening
                min_delay = 2.0
            else:  # Late night/early morning
                min_delay = 1.5
            
            if time_since_last < min_delay:
                await asyncio.sleep(min_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Progressive breaks
        if self.request_count % 30 == 0:
            break_duration = random.uniform(45, 120)
            print(f"Taking a {break_duration:.0f}s break after {self.request_count} requests...")
            await asyncio.sleep(break_duration)
        
        # Session reset after many requests
        if self.request_count % 100 == 0:
            print("Session reset - taking extended break...")
            await asyncio.sleep(random.uniform(300, 600))  # 5-10 minutes

    async def crawl(self):
        self.session_start_time = time.time()
        
        async with async_playwright() as p:
            print("Launching advanced stealth browser...")
            context = await self.create_advanced_stealth_context(p)
            page = await context.new_page()
            
            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
            elif len(self.people) > 0:
                self.queue = list(self.people.keys())[:100]
                random.shuffle(self.queue)
            else:
                print("No start root found. Please provide a URL with &rootIndividualID=")
                return

            print("Starting advanced stealth scrape...")
            
            hop = 0
            consecutive_no_new = 0
            error_count = 0

            try:
                while self.queue and error_count < 10:
                    root_id = self.queue.pop(0)
                    
                    if root_id in self.visited_roots:
                        continue
                    
                    self.visited_roots.add(root_id)
                    hop += 1
                    
                    # Intelligent rate limiting
                    await self.intelligent_rate_limit()
                    
                    # Construct URL
                    target_url = f"https://www.myheritage.co.il/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                    
                    print(f"[{hop}] Visiting {root_id}... (Collected: {len(self.people)})")
                    
                    try:
                        # Pre-navigation human behavior
                        await self.simulate_advanced_human_behavior(page)
                        
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
                        
                        # Post-load human behavior
                        await asyncio.sleep(random.uniform(1, 3))
                        await self.simulate_advanced_human_behavior(page)
                        
                        # Wait for content with realistic timing
                        try:
                            await page.wait_for_selector(".person-card", timeout=10000)
                        except:
                            await asyncio.sleep(random.uniform(3, 6))

                        # Extract data
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
                        
                        # Process data
                        for pid, pdata in data['people'].items():
                            if pid not in self.people:
                                self.people[pid] = pdata
                                new_in_batch += 1
                                if pid not in self.visited_roots and pid not in self.queue:
                                    self.queue.append(pid)

                        for fid, fdata in data['families'].items():
                            self.families[fid] = fdata
                            for rel in [fdata.get('h'), fdata.get('w')] + (fdata.get('c') or []):
                                if rel:
                                    rid = str(rel)
                                    if rid not in self.visited_roots and rid not in self.queue:
                                        self.queue.append(rid)

                        if new_in_batch > 0:
                            print(f"    Found +{new_in_batch} new people.")
                            consecutive_no_new = 0
                            error_count = 0
                        else:
                            consecutive_no_new += 1
                        
                        # Adaptive delays and queue management
                        delay = self.get_realistic_delay()
                        
                        if consecutive_no_new > 7:
                            print("    Stuck in known area. Aggressive shuffle...")
                            random.shuffle(self.queue)
                            # Add some random IDs to explore new areas
                            if len(self.people) > 50:
                                random_people = random.sample(list(self.people.keys()), 20)
                                self.queue.extend(random_people)
                            consecutive_no_new = 0
                            delay = random.uniform(15, 30)
                        
                        # Periodic saves
                        if hop % 20 == 0:
                            self.save_state()
                            print(f"    Saved data. (Total: {len(self.people)})")

                        await asyncio.sleep(delay)

                    except Exception as e:
                        error_count += 1
                        print(f"    Error visiting {root_id}: {e}")
                        await asyncio.sleep(random.uniform(10, 20))
                        
                        if error_count >= 10:
                            print("Too many errors, stopping scrape...")
                            break

            except KeyboardInterrupt:
                print("Stopping scrape...")
            finally:
                self.save_state()
                print(f"Done. Final count: {len(self.people)} people collected.")
                await context.close()

if __name__ == "__main__":
    import time
    
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
    
    # Enable proxy by setting use_proxy=True and adding proxies to ProxyRotator
    scraper = AdvancedStealthScraper(url, use_proxy=False)
    scraper.load_state()
    asyncio.run(scraper.crawl())