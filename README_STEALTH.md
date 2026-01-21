# Stealth Web Scraping Configuration

## Installation Requirements

```bash
pip install playwright aiohttp
playwright install chromium
```

## Anti-Detection Features Implemented

### 1. **Browser Fingerprint Randomization**
- Rotating user agents (Chrome, Firefox, Edge)
- Random viewport sizes
- Variable browser languages and locales
- Different timezone IDs
- Canvas fingerprint randomization
- WebGL parameter spoofing

### 2. **Human-Like Behavior Simulation**
- Natural mouse movements with Bezier curves
- Random scrolling patterns
- Occasional keyboard interactions (Tab key)
- Variable timing between actions
- Realistic click patterns

### 3. **Advanced Rate Limiting**
- Time-based delay adjustments
- Business hours vs late night timing
- Session fatigue simulation
- Progressive breaks (every 30 requests)
- Extended session resets (every 100 requests)

### 4. **Request Header Optimization**
- Complete HTTP header set
- sec-ch-ua headers for Chrome
- Proper Accept-Language chains
- DNT (Do Not Track) headers
- Cache-Control headers

### 5. **Browser Configuration**
- Headless mode with anti-automation flags
- Disabled automation detection
- WebGL and canvas spoofing
- Chrome runtime mocking
- Permissions API override

### 6. **Proxy Support** (Optional)
- Proxy rotation capability
- Support for authenticated proxies
- Easy proxy configuration

## Usage

### Basic Stealth Scraping
```python
from stealth_scraper import StealthScraper

scraper = StealthScraper("your_url_here")
scraper.load_state()
asyncio.run(scraper.crawl())
```

### Advanced Scraping with Proxy
```python
from advanced_stealth_scraper import AdvancedStealthScraper

# Add proxies
scraper = AdvancedStealthScraper("your_url_here", use_proxy=True)
scraper.proxy_rotator.add_proxy("http://proxy1:port", "username", "password")
scraper.proxy_rotator.add_proxy("http://proxy2:port")

scraper.load_state()
asyncio.run(scraper.crawl())
```

## Detection Avoidance Strategies

### 1. **Timing Patterns**
- Normal distribution delays (mean 12s, std dev 4s)
- Time-based adjustments (slower during business hours)
- Occasional long breaks (60-180s)
- Session fatigue simulation

### 2. **Request Patterns**
- Random queue shuffling
- Intelligent exploration when stuck
- Variable save intervals
- Error recovery with backoff

### 3. **Browser Behavior**
- Natural mouse movements
- Realistic scrolling
- Random viewport changes
- Proper header sequences

## Configuration Options

### Delay Ranges
- **Basic**: 5-25 seconds between requests
- **Advanced**: Time-adaptive with session fatigue
- **Breaks**: 45-120s every 30 requests
- **Session Resets**: 5-10 minutes every 100 requests

### Success Metrics
- **Low Detection**: <1% CAPTCHA rate
- **High Success**: >95% request success rate
- **Data Quality**: Complete data extraction

## Monitoring and Maintenance

### Key Indicators
- Request success rate
- CAPTCHA frequency
- Response time patterns
- Data completeness

### Optimization Tips
1. Monitor error rates and adjust delays
2. Rotate proxies if IP blocks occur
3. Update user agents periodically
4. Adjust timing based on target site behavior

## Security Considerations

- Always respect robots.txt
- Implement proper rate limiting
- Use proxies for production scraping
- Monitor for detection patterns
- Have backup strategies ready

## Troubleshooting

### Common Issues
1. **High CAPTCHA rate** → Increase delays, rotate user agents
2. **IP blocks** → Enable proxy rotation
3. **Slow extraction** → Optimize selectors, reduce waits
4. **Memory issues** → Implement data streaming

### Performance Tuning
- Adjust concurrent requests
- Optimize data extraction
- Implement caching
- Use connection pooling