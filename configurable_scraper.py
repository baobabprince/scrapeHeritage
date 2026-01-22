import asyncio
import json
import os
import random
import time
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page

class ConfigurableMyHeritageScraper:
    def __init__(self, config_file: str = "config_secrets.txt"):
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Set instance variables
        self.email = self.config["EMAIL"]
        self.password = self.config["PASSWORD"]
        self.target_url = self.config["TARGET_URL"]
        self.output_dir = self.config["OUTPUT_DIR"]
        self.site_id = self.config["SITE_ID"]
        self.tree_id = self.config["TREE_ID"]
        self.start_root = self.config["START_ROOT_ID"]
        
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
        
        print("Configuration loaded:")
        print(f"   Email: {self.email}")
        print(f"   Target: Site={self.site_id}, Tree={self.tree_id}, Root={self.start_root}")
        
        # Check if using Gmail
        if "gmail.com" in self.email:
            print("   NOTE: For Gmail, use App Password instead of regular password")
            print("   Get App Password: Google Account → Security → 2-Step Verification → App Passwords")
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from file"""
        config = {}
        current_section = None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Handle different value types
                    if value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)
                    elif value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    
                    config[key] = value
        
        return config
    
    async def login(self, context: BrowserContext) -> bool:
        """Login using configuration and debug mode"""
        show_browser = self.config.get("SHOW_BROWSER", False)
        debug = self.config.get("DEBUG_MODE", True)
        
        page = await context.new_page()
        
        try:
            if debug:
                print(f"🔐 Logging in as {self.email}...")
            
            # Go to login page
            domain = self.config.get("CURRENT_DOMAIN", "www.myheritage.co.il")
            login_url = f"https://{domain}/login"
            
            await page.goto(login_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # Fill credentials
            await page.fill('input[name="registrationEmail"]', self.email)
            await page.fill('input[name="registrationLoginPassword"]', self.password)
            
            if debug:
                print("📝 Credentials filled")
            
            await asyncio.sleep(1)
            
            # Try multiple login methods
            login_success = False
            
            # Method 1: Direct button click
            try:
                await page.click('button.registration_cta--XiPIY', timeout=5000)
                login_success = True
                if debug:
                    print("✅ Method 1: Direct button click successful")
            except:
                if debug:
                    print("❌ Method 1 failed")
            
            # Method 2: JavaScript click
            if not login_success:
                try:
                    await page.evaluate("""
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.className.includes('registration_cta')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    login_success = True
                    if debug:
                        print("✅ Method 2: JavaScript click successful")
                except:
                    if debug:
                        print("❌ Method 2 failed")
            
            # Method 3: Form submit
            if not login_success:
                try:
                    await page.press('input[name="registrationLoginPassword"]', 'Enter')
                    login_success = True
                    if debug:
                        print("✅ Method 3: Form submit successful")
                except:
                    if debug:
                        print("❌ Method 3 failed")
            
            if not login_success:
                if debug:
                    print("❌ All login methods failed")
                await page.close()
                return False
            
            # Wait for login to complete
            if debug:
                print("⏳ Waiting for login completion...")
            await asyncio.sleep(15)
            
            # Check if successful
            current_url = page.url
            if debug:
                print(f"📍 Current URL: {current_url}")
            
            if "login" not in current_url and "myheritage" in current_url:
                if debug:
                    print("✅ Login successful!")
                await page.close()
                return True
            else:
                # Check for CAPTCHA
                captcha = await page.query_selector_all('[class*="captcha"], [id*="captcha"], [class*="challenge"]')
                if captcha and debug:
                    print("🚫 CAPTCHA detected - may need manual intervention")
                elif debug:
                    print("❌ Login failed - check credentials")
                
                await page.close()
                return False
                
        except Exception as e:
            if debug:
                print(f"❌ Login error: {e}")
            await page.close()
            return False
    
    async def create_stealth_context(self, playwright) -> BrowserContext:
        """Create browser context from configuration"""
        headless = self.config.get("HEADLESS", True)
        
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        user_agent = random.choice(self.config.get("USER_AGENTS", []))
        viewport = random.choice(self.config.get("VIEWPORTS", []))
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale=self.config.get("DEFAULT_LANGUAGE", "en-US"),
            timezone_id=self.config.get("DEFAULT_TIMEZONE", "America/New_York"),
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        return browser, context
    
    def get_delay(self) -> float:
        """Get delay from configuration with variation"""
        base_delay = self.config.get("BASE_DELAY", 12)
        std_dev = self.config.get("DELAY_STD_DEV", 4)
        min_delay = self.config.get("MIN_DELAY", 5)
        max_delay = self.config.get("MAX_DELAY", 25)
        
        # Normal distribution with bounds
        delay = random.gauss(base_delay, std_dev)
        delay = max(min_delay, min(max_delay, delay))
        
        # Occasional long breaks
        if random.random() < 0.1:
            delay += random.uniform(60, 180)
        
        return delay
    
    async def crawl(self):
        async with async_playwright() as p:
            debug = self.config.get("DEBUG_MODE", True)
            max_hops = self.config.get("MAX_HOPS", 1000)
            save_interval = self.config.get("SAVE_INTERVAL", 20)
            
            if debug:
                print("🚀 Creating stealth browser...")
            
            browser, context = await self.create_stealth_context(p)
            
            # Login first
            if not await self.login(context):
                print("❌ Authentication failed")
                await browser.close()
                return
            
            page = await context.new_page()
            
            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
                if debug:
                    print(f"🎯 Starting with root ID: {self.start_root}")
            else:
                print("❌ No start root found")
                await browser.close()
                return

            if debug:
                print("🔄 Starting authenticated crawl...")

            hop = 0
            try:
                while self.queue and hop < max_hops:
                    root_id = self.queue.pop(0)
                    
                    if root_id in self.visited_roots:
                        continue
                    
                    self.visited_roots.add(root_id)
                    hop += 1
                    
                    # Rate limiting
                    delay = self.get_delay()
                    if debug:
                        print(f"⏱️  Waiting {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    
                    # Construct URL
                    domain = self.config.get("CURRENT_DOMAIN", "www.myheritage.co.il")
                    target_url = f"https://{domain}/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                    
                    if debug:
                        print(f"[{hop}] 🔍 Visiting {root_id}... (Collected: {len(self.people)})")
                    
                    try:
                        await page.goto(target_url, wait_until="networkidle", timeout=60000)
                        await asyncio.sleep(3)
                        
                        # Check if still logged in
                        current_url = page.url
                        if "login" in current_url:
                            if debug:
                                print("🔄 Logged out, re-authenticating...")
                            await self.login(context)
                            await page.goto(target_url, wait_until="networkidle", timeout=60000)
                            await asyncio.sleep(3)
                        
                        # Extract data
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
                            print(f"    ✅ Found +{new_in_batch} new people. Queue: {len(self.queue)}")
                        else:
                            print(f"    ℹ️  No new people. Queue: {len(self.queue)}")
                        
                        # Save periodically
                        if hop % save_interval == 0:
                            self.save_data()
                            print(f"    💾 Saved. Total: {len(self.people)}")
                        
                    except Exception as e:
                        print(f"    ❌ Error visiting {root_id}: {e}")
                        await asyncio.sleep(5)
                        
            except KeyboardInterrupt:
                print("⛔ Stopping scrape...")
            finally:
                self.save_data()
                print(f"✅ Done. Collected {len(self.people)} people.")
                await browser.close()
    
    def save_data(self):
        """Save collected data"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({
                    "siteId": self.site_id,
                    "treeId": self.tree_id,
                    "personCards": list(self.people.values()),
                    "familyConnectors": list(self.families.values())
                }, f, ensure_ascii=False, indent=2)
            
            if self.config.get("DEBUG_MODE", True):
                print(f"💾 Data saved to {self.data_file}")
        except Exception as e:
            print(f"❌ Error saving data: {e}")

if __name__ == "__main__":
    print("MyHeritage Configurable Stealth Scraper")
    print("Loading configuration from config_secrets.txt")
    
    # Check if config file exists
    if not os.path.exists("config_secrets.txt"):
        print("❌ Error: config_secrets.txt not found!")
        print("📝 Please create this file with your credentials (see config_secrets.txt.example)")
    else:
        scraper = ConfigurableMyHeritageScraper()
        asyncio.run(scraper.crawl())