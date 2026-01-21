# MyHeritage Account Creation Instructions

## Quick Manual Account Setup (Recommended)

1. **Visit**: https://www.myheritage.com
2. **Click**: "Sign Up" or "Start free trial"
3. **Fill form**:
   - Email: Use a real email address
   - Password: Create a password
   - Name: Use any name (John Smith is fine)
   - Birth year: Any year (e.g., 1980)
4. **Verify** email if required
5. **Login** to confirm account works

## Update Scraper Credentials

Edit `simple_auth_scraper.py` and update:
```python
EMAIL = "your_real_email@example.com"  # Your actual email
PASSWORD = "your_actual_password"      # Your actual password
```

## Run Scraper

```bash
python simple_auth_scraper.py
```

## Features

✅ **Authenticated scraping** - Access to full tree data
✅ **Anti-detection** - Stealth browser with delays
✅ **Session management** - Automatic re-login if needed  
✅ **Human behavior** - Random delays and interactions
✅ **Error recovery** - Handles logout/block scenarios

## Why Login Required

MyHeritage restricts family tree data to logged-in users only. Without authentication:
- localStorage remains empty
- No family tree data accessible
- Scraping returns 0 people

With proper authentication:
- Full tree data becomes available
- localStorage populated with family connections
- Can access all person/family relationships

## Testing Mode

The scraper runs in visible mode for debugging. Set `headless=True` in the code for production use.