import asyncio
import json
import os
import random
from playwright.async_api import async_playwright

async def debug_scrape():
    """Debug version to see what's actually happening"""
    
    site_id = "OYYV76FKVHAB6KC7YBFWOXCTQTUXUTI"
    tree_id = "1"
    root_id = "1500918"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        target_url = f"https://www.myheritage.co.il/family-trees/x/{site_id}?familyTreeID={tree_id}&rootIndividualID={root_id}"
        
        print(f"Visiting: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            print("Page loaded, waiting for content...")
            await asyncio.sleep(5)
            
            # Check localStorage content
            storage = await page.evaluate("""
                (() => {
                    let storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        if (key && key.includes('get-tree-layout.php')) {
                            try {
                                let data = JSON.parse(localStorage.getItem(key));
                                storage[key] = {
                                    hasPersonCards: !!data.personCards,
                                    personCount: data.personCards ? data.personCards.length : 0,
                                    hasFamilyConnectors: !!data.familyConnectors,
                                    familyCount: data.familyConnectors ? data.familyConnectors.length : 0
                                };
                            } catch(e) {
                                storage[key] = {error: e.message};
                            }
                        }
                    }
                    return storage;
                })()
            """)
            
            print("\n=== LocalStorage Analysis ===")
            for key, info in storage.items():
                print(f"Key: {key}")
                print(f"  People: {info.get('personCount', 0)}")
                print(f"  Families: {info.get('familyCount', 0)}")
                print()
            
            # Get actual data if found
            data = await page.evaluate("""
                (() => {
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
                })()
            """)
            
            print(f"Found {len(data['people'])} people and {len(data['families'])} families")
            
            if len(data['people']) > 0:
                first_person = list(data['people'].values())[0]
                print(f"First person: {first_person.get('n', 'Unknown')} (ID: {first_person.get('id')})")
                
                # Check family connections
                for fid, fdata in list(data['families'].items())[:3]:
                    print(f"Family {fid}: husband={fdata.get('h')}, wife={fdata.get('w')}, children={fdata.get('c', [])}")
            
            # Check if person cards are visible
            cards = await page.query_selector_all(".person-card")
            print(f"Visible person cards on page: {len(cards)}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scrape())