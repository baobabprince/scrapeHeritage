import asyncio
import json
import os
import random
import time
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Page

class MyHeritageAuth:
    def __init__(self, output_dir: str = "auth_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.session_file = os.path.join(output_dir, "myheritage_session.json")
        
    def generate_user_data(self) -> dict:
        """Generate random user data for registration"""
        first_names = ["David", "Sarah", "Michael", "Emma", "John", "Lisa", "Robert", "Anna"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@temp-mail.org",
            "password": f"ScrapingPass{random.randint(100, 999)}!",
            "birth_year": random.randint(1950, 1990),
            "gender": random.choice(["male", "female"])
        }
    
    async def register_account(self, browser_context: BrowserContext) -> Optional[dict]:
        """Register a new MyHeritage account"""
        page = await browser_context.new_page()
        
        try:
            print("Registering new MyHeritage account...")
            
            # Go to signup page
            await page.goto("https://www.myheritage.com/", wait_until="networkidle", timeout=30000)
            
            # Click "Sign Up" button
            await page.wait_for_selector('[data-testid="signup-button"], a[href*="signup"], button:has-text("Sign Up")', timeout=10000)
            await page.click('[data-testid="signup-button"], a[href*="signup"], button:has-text("Sign Up")')
            
            # Wait for registration form
            await page.wait_for_selector('input[name*="email"], input[type="email"]', timeout=10000)
            
            user_data = self.generate_user_data()
            print(f"Generated user: {user_data['email']}")
            
            # Fill registration form
            await page.fill('input[name*="email"], input[type="email"]', user_data["email"])
            
            # Look for password field
            password_selectors = ['input[name*="password"]', 'input[type="password"]', 'input[placeholder*="password"]']
            for selector in password_selectors:
                try:
                    await page.fill(selector, user_data["password"])
                    break
                except:
                    continue
            
            # Look for first name field
            first_name_selectors = ['input[name*="firstName"]', 'input[name*="first_name"]', 'input[placeholder*="first"]']
            for selector in first_name_selectors:
                try:
                    await page.fill(selector, user_data["first_name"])
                    break
                except:
                    continue
            
            # Look for last name field  
            last_name_selectors = ['input[name*="lastName"]', 'input[name*="last_name"]', 'input[placeholder*="last"]']
            for selector in last_name_selectors:
                try:
                    await page.fill(selector, user_data["last_name"])
                    break
                except:
                    continue
            
            # Select gender
            try:
                await page.click(f'input[value="{user_data["gender"]}"], label:has-text("{user_data["gender"].title()}")')
            except:
                pass
            
            # Select birth year
            try:
                await page.select_option('select[name*="year"], select[name*="birth"]', str(user_data["birth_year"]))
            except:
                pass
            
            # Accept terms
            try:
                await page.check('input[type="checkbox"][name*="terms"], input[type="checkbox"][name*="agree"]')
            except:
                pass
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign Up")',
                'button:has-text("Create Account")',
                'button:has-text("Continue")',
                '[data-testid="signup-submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    break
                except:
                    continue
            
            # Wait for registration to complete
            await asyncio.sleep(5)
            
            # Check if successful (redirected to main site)
            current_url = page.url
            if "myheritage" in current_url and "login" not in current_url:
                print("✅ Account registration successful!")
                return user_data
            else:
                print("❌ Registration may have failed")
                return None
                
        except Exception as e:
            print(f"Registration error: {e}")
            return None
        
        finally:
            await page.close()
    
    async def login(self, browser_context: BrowserContext, email: str, password: str) -> bool:
        """Login to MyHeritage account"""
        page = await browser_context.new_page()
        
        try:
            print(f"Logging in as {email}...")
            
            # Go to login page
            await page.goto("https://www.myheritage.co.il/login", wait_until="networkidle", timeout=30000)
            
            # Fill login form
            await page.fill('input[name*="email"], input[type="email"]', email)
            
            password_selectors = ['input[name*="password"]', 'input[type="password"]']
            for selector in password_selectors:
                try:
                    await page.fill(selector, password)
                    break
                except:
                    continue
            
            # Submit login
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Login")',
                'button:has-text("כניסה")',
                'input[type="submit"]'
            ]
            
            for selector in login_selectors:
                try:
                    await page.click(selector)
                    break
                except:
                    continue
            
            # Wait for login to complete
            await asyncio.sleep(10)
            
            # Check if successful
            current_url = page.url
            if "login" not in current_url and "myheritage" in current_url:
                print("✅ Login successful!")
                
                # Save session cookies
                cookies = await browser_context.cookies()
                self.save_session(email, password, cookies)
                
                await page.close()
                return True
            else:
                print("❌ Login failed")
                await page.close()
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            await page.close()
            return False
    
    def save_session(self, email: str, password: str, cookies: list):
        """Save session data for reuse"""
        session_data = {
            "email": email,
            "password": password,
            "cookies": cookies,
            "timestamp": time.time()
        }
        
        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)
        
        print(f"Session saved for {email}")
    
    def load_session(self) -> Optional[dict]:
        """Load existing session data"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                    
                # Check if session is recent (less than 24 hours old)
                if time.time() - session_data.get("timestamp", 0) < 86400:
                    print(f"Found existing session for {session_data['email']}")
                    return session_data
            except:
                pass
        
        return None
    
    async def ensure_authenticated(self, browser_context: BrowserContext) -> bool:
        """Ensure browser is authenticated (register new account if needed)"""
        # Try to load existing session
        session = self.load_session()
        
        if session:
            # Try to use existing session
            await browser_context.add_cookies(session["cookies"])
            
            # Test if session is still valid
            page = await browser_context.new_page()
            try:
                await page.goto("https://www.myheritage.co.il/", wait_until="networkidle", timeout=30000)
                
                # Check if we're logged in
                current_url = page.url
                if "login" not in current_url:
                    print("✅ Existing session is valid")
                    await page.close()
                    return True
                    
            except:
                pass
            
            await page.close()
            print("❌ Existing session expired")
        
        # Need to register new account
        user_data = await self.register_account(browser_context)
        
        if user_data:
            return await self.login(browser_context, user_data["email"], user_data["password"])
        
        return False


class AuthenticatedStealthScraper:
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
        
        # Auth handler
        self.auth = MyHeritageAuth()
        
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
    
    async def create_authenticated_stealth_context(self, playwright) -> BrowserContext:
        """Create stealth browser context with authentication"""
        user_agent = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
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
        
        # Ensure authentication
        if not await self.auth.ensure_authenticated(context):
            raise Exception("Failed to authenticate")
        
        return context
    
    async def crawl(self):
        async with async_playwright() as p:
            print("Creating authenticated stealth browser...")
            context = await self.create_authenticated_stealth_context(p)
            page = await context.new_page()
            
            # Seed queue
            if self.start_root:
                self.queue = [self.start_root]
                print(f"Starting with root ID: {self.start_root}")
            else:
                print("No start root found. Please provide a URL with &rootIndividualID=")
                return

            print("Starting authenticated stealth scrape...")
            
            hop = 0
            try:
                while self.queue and hop < 10:  # Limit for testing
                    root_id = self.queue.pop(0)
                    
                    if root_id in self.visited_roots:
                        continue
                    
                    self.visited_roots.add(root_id)
                    hop += 1
                    
                    # Rate limiting
                    delay = random.uniform(5, 15)
                    await asyncio.sleep(delay)
                    
                    # Construct URL
                    target_url = f"https://www.myheritage.co.il/family-trees/x/{self.site_id}?familyTreeID={self.tree_id}&rootIndividualID={root_id}"
                    
                    print(f"[{hop}] Visiting {root_id}... (Collected: {len(self.people)})")
                    
                    try:
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
                        
                        print(f"    DEBUG: Found {len(data['people'])} people, {len(data['families'])} families")
                        
                        new_in_batch = 0
                        
                        # Process data
                        for pid, pdata in data['people'].items():
                            if pid not in self.people:
                                self.people[pid] = pdata
                                new_in_batch += 1
                                print(f"    Added person {pid}")
                                
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
                        
                        await asyncio.sleep(random.uniform(3, 8))
                        
                    except Exception as e:
                        print(f"    Error visiting {root_id}: {e}")
                        await asyncio.sleep(5)
                        
            except KeyboardInterrupt:
                print("Stopping scrape...")
            finally:
                print(f"Done. Collected {len(self.people)} people.")
                await context.close()

if __name__ == "__main__":
    url = "https://www.myheritage.co.il/family-trees/%D7%9E%D7%94%D7%95%D7%9C%D7%9C/OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI?familyTreeID=1&rootIndividualID=1500918"
    scraper = AuthenticatedStealthScraper(url, output_dir="auth_output")
    asyncio.run(scraper.crawl())