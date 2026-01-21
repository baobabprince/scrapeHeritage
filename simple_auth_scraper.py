import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright, BrowserContext, Page

class SimpleMyHeritageScraper:
    def __init__(self, tree_url: str, email: str, password: str, output_dir: str = "output"):
        self.url = tree_url
        self.email = email
        self.password = password
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
    
    async def login(self, context: BrowserContext) -> bool:
        """Login to MyHeritage"""
        page = await context.new_page()
        
        try:
            print(f"Logging in as {self.email}...")
            
            # Go to login page
            await page.goto("https://www.myheritage.co.il/login", wait_until="networkidle", timeout=30000)
            
            # Wait for page to load completely
            await asyncio.sleep(3)
            
            # Try different email field selectors
            email_selectors = [
                'input[name="registrationEmail"]',
                'input[id="registrationEmail"]',
                'input[name="email"]',
                'input[type="email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, self.email)
                    email_filled = True
                    print(f"Filled email with selector: {selector}")
                    break
                except:
                    continue
            
            if not email_filled:
                print("Could not find email field")
                await page.close()
                return False
            
            # Try different password field selectors
            password_selectors = [
                'input[name="registrationLoginPassword"]',
                'input[id="registrationLoginPassword"]',
                'input[name="password"]',
                'input[type="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, self.password)
                    password_filled = True
                    print(f"Filled password with selector: {selector}")
                    break
                except:
                    continue
            
            if not password_filled:
                print("Could not find password field")
                await page.close()
                return False
            
            await asyncio.sleep(1)
            
            # Try different login button selectors
            login_selectors = [
                'button.registration_cta--XiPIY',
                '[class*="registration_cta"]',
                '.registration_cta--XiPIY',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    login_clicked = True
                    print(f"Clicked login with selector: {selector}")
                    break
                except:
                    continue
            
            if not login_clicked:
                # Try JavaScript approach
                try:
                    print("Trying JavaScript login button click...")
                    await page.evaluate("""
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.className.includes('registration_cta') || btn.className.includes('login')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    login_clicked = True
                    print("Clicked login via JavaScript")
                except:
                    pass
            
            if not login_clicked:
                print("Could not find/click login button")
                await page.close()
                return False
            
            # Wait for login to complete
            print("Waiting for login to complete...")
            await asyncio.sleep(15)
            
            # Check if successful
            current_url = page.url
            print(f"Current URL after login: {current_url}")
            
            if "login" not in current_url and "myheritage" in current_url:
                print("Login successful!")
                await page.close()
                return True
            else:
                # Check for CAPTCHA or other issues
                captcha = await page.query_selector_all('[class*="captcha"], [id*="captcha"]')
                if captcha:
                    print("CAPTCHA detected - login blocked")
                else:
                    print("Login failed - check credentials")
                
                await page.close()
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            await page.close()
            return False
    
    async def crawl(self):
        async with async_playwright() as p:
            print("Creating browser context...")
            browser = await p.chromium.launch(
                headless=False,  # Show browser for debugging
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
            )
            
            # Add basic stealth
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Login first
            if not await self.login(context):
                print("Authentication failed")
                await browser.close()
                return
            
            page = await context.new_page()
            
            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
                print(f"Starting with root ID: {self.start_root}")
            else:
                print("No start root found. Please provide a URL with &rootIndividualID=")
                return

            print("Starting authenticated scrape...")
            
            hop = 0
            try:
                while self.queue and hop < 5:  # Limit for testing
                    root_id = self.queue.pop(0)
                    
                    if root_id in self.visited_roots:
                        continue
                    
                    self.visited_roots.add(root_id)
                    hop += 1
                    
                    # Rate limiting
                    delay = random.uniform(8, 15)
                    await asyncio.sleep(delay)
                    
                    # Construct URL
                    target_url = f"https://www.myheritage.co.il/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                    
                    print(f"[{hop}] Visiting {root_id}... (Collected: {len(self.people)})")
                    
                    try:
                        await page.goto(target_url, wait_until="networkidle", timeout=60000)
                        await asyncio.sleep(5)
                        
                        # Check if we're still logged in
                        current_url = page.url
                        if "login" in current_url:
                            print("Logged out during scraping, need to re-login")
                            await self.login(context)
                            await page.goto(target_url, wait_until="networkidle", timeout=60000)
                            await asyncio.sleep(5)
                        
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
                        
                        print(f"    Found {len(data['people'])} people, {len(data['families'])} families")
                        
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
                            print(f"    Found +{new_in_batch} new people. Queue: {len(self.queue)}")
                        else:
                            print(f"    No new people. Queue: {len(self.queue)}")
                        
                    except Exception as e:
                        print(f"    Error visiting {root_id}: {e}")
                        await asyncio.sleep(5)
                        
            except KeyboardInterrupt:
                print("Stopping scrape...")
            finally:
                print(f"Done. Collected {len(self.people)} people.")
                self.save_data()
                await browser.close()
    
    def save_data(self):
        """Save collected data"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({
                "siteId": self.site_id,
                "treeId": self.tree_id,
                "personCards": list(self.people.values()),
                "familyConnectors": list(self.families.values())
            }, f, ensure_ascii=False, indent=2)
        
        print(f"Data saved to {self.data_file}")

if __name__ == "__main__":
    # You need to provide actual MyHeritage credentials
    # Option 1: Create account manually at myheritage.com first
    # Option 2: Use existing credentials
    
    print("=== MyHeritage Authenticated Scraper ===")
    print("You need to provide login credentials:")
    print("1. Create a free account at https://www.myheritage.com")
    print("2. Update the credentials below")
    print()
    
    # Credentials provided
    EMAIL = "microbiomec@gmail.com"  # UPDATE THIS
    PASSWORD = "auutrnv23"           # UPDATE THIS
    
    if EMAIL == "your_email@example.com":
        print("Please update EMAIL and PASSWORD in script")
        print("Create a free account first, then update credentials")
    else:
        url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
        scraper = SimpleMyHeritageScraper(url, EMAIL, PASSWORD, output_dir="authenticated_output")
        asyncio.run(scraper.crawl())