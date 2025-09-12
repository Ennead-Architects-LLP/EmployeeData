#!/usr/bin/env python3
"""
Advanced Selector Recorder with Authentication and Dynamic Loading
Handles login, waits for dynamic content, and records optimal selectors
"""

import asyncio
import json
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

class AdvancedSelectorRecorder:
    def __init__(self):
        self.browser = None
        self.page = None
        self.capture_dir = "debug/dom_captures"
        self.employee_url = "https://ei.ennead.com/employee-directory"
        
    async def start_browser(self):
        """Start browser with debugging options"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            slow_mo=500,     # Slow down for observation
            devtools=True    # Open dev tools
        )
        
        # Create context with realistic user agent
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        self.page = await context.new_page()
        
        # Enable request/response logging
        self.page.on("request", lambda req: print(f"🌐 REQ: {req.method} {req.url}"))
        self.page.on("response", lambda res: print(f"📥 RES: {res.status} {res.url}"))
        
    async def navigate_and_wait(self):
        """Navigate to page and wait for content to load"""
        print(f"🌐 Navigating to: {self.employee_url}")
        
        try:
            # Navigate to the page
            await self.page.goto(self.employee_url, wait_until="domcontentloaded")
            
            # Wait for potential login redirect or dynamic content
            print("⏳ Waiting for page to fully load...")
            await self.page.wait_for_timeout(5000)
            
            # Check if we're on a login page
            current_url = self.page.url
            print(f"📍 Current URL: {current_url}")
            
            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("🔐 Login page detected - manual login required")
                print("   Please log in manually in the browser window...")
                print("   Press Enter when logged in and page is loaded...")
                input()
            
            # Wait for dynamic content to load
            print("⏳ Waiting for dynamic content...")
            await self.page.wait_for_timeout(3000)
            
            # Try to wait for common loading indicators to disappear
            try:
                await self.page.wait_for_selector(".loading, .spinner, [data-loading]", state="hidden", timeout=5000)
            except:
                pass  # No loading indicators found
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False
    
    async def analyze_page_structure(self):
        """Analyze the page structure and find all possible selectors"""
        print("🔍 Analyzing page structure...")
        
        # Get all elements with classes
        all_elements = await self.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const classMap = {};
                const tagMap = {};
                const linkMap = {};
                
                elements.forEach(el => {
                    // Count by class
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(' ').forEach(cls => {
                            if (cls.trim()) {
                                classMap[cls] = (classMap[cls] || 0) + 1;
                            }
                        });
                    }
                    
                    // Count by tag
                    const tag = el.tagName.toLowerCase();
                    tagMap[tag] = (tagMap[tag] || 0) + 1;
                    
                    // Count links
                    if (el.tagName === 'A' && el.href) {
                        if (el.href.includes('employee') || el.href.includes('person') || el.href.includes('profile')) {
                            linkMap[el.href] = (linkMap[el.href] || 0) + 1;
                        }
                    }
                });
                
                return {
                    classes: classMap,
                    tags: tagMap,
                    employeeLinks: Object.keys(linkMap)
                };
            }
        """)
        
        print(f"📊 Found {len(all_elements['classes'])} unique classes")
        print(f"📊 Found {len(all_elements['tags'])} unique tags")
        print(f"📊 Found {len(all_elements['employeeLinks'])} employee links")
        
        # Save analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = f"{self.capture_dir}/page_structure_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(all_elements, f, indent=2)
        print(f"💾 Saved page structure to: {analysis_file}")
        
        return all_elements
    
    async def test_employee_selectors(self, page_structure):
        """Test various selectors for employee elements"""
        print("🧪 Testing employee selectors...")
        
        # Get top classes that might contain employees
        top_classes = sorted(page_structure['classes'].items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Test selectors
        selectors_to_test = []
        
        # Add top classes
        for class_name, count in top_classes:
            if count > 1:  # Only classes with multiple elements
                selectors_to_test.append(f".{class_name}")
        
        # Add common patterns
        common_patterns = [
            "div[class*='employee']",
            "div[class*='person']", 
            "div[class*='staff']",
            "div[class*='team']",
            "div[class*='card']",
            "div[class*='item']",
            "div[class*='list']",
            "a[href*='employee']",
            "a[href*='person']",
            "a[href*='profile']",
            "tr",  # Table rows
            "td",  # Table cells
            "li",  # List items
        ]
        selectors_to_test.extend(common_patterns)
        
        # Test each selector
        results = {}
        for selector in selectors_to_test:
            try:
                elements = await self.page.query_selector_all(selector)
                count = len(elements)
                
                if count > 0:
                    # Analyze elements
                    element_info = []
                    for i, element in enumerate(elements[:5]):  # Sample first 5
                        try:
                            tag = await element.evaluate("el => el.tagName")
                            classes = await element.get_attribute("class") or ""
                            href = await element.get_attribute("href") or ""
                            text = await element.inner_text() or ""
                            
                            element_info.append({
                                "tag": tag,
                                "classes": classes,
                                "href": href[:100],
                                "text": text[:50].strip()
                            })
                        except:
                            pass
                    
                    results[selector] = {
                        "count": count,
                        "found": True,
                        "samples": element_info
                    }
                    
                    print(f"✅ {selector}: {count} elements")
                    if element_info:
                        sample = element_info[0]
                        print(f"   Sample: <{sample['tag']}> {sample['text'][:30]}...")
                else:
                    results[selector] = {"count": 0, "found": False}
                    
            except Exception as e:
                results[selector] = {"count": 0, "found": False, "error": str(e)}
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"{self.capture_dir}/selector_test_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Saved selector test results to: {results_file}")
        
        return results
    
    async def capture_employee_data(self, best_selectors):
        """Capture actual employee data using best selectors"""
        print(f"📸 Capturing employee data...")
        
        employee_data = []
        
        for selector in best_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"Testing {selector}: {len(elements)} elements")
                
                for i, element in enumerate(elements):
                    try:
                        # Extract employee information
                        data = await element.evaluate("""
                            (el) => {
                                const href = el.href || '';
                                const text = el.innerText || '';
                                const classes = el.className || '';
                                
                                // Look for name patterns
                                const nameMatch = text.match(/([A-Z][a-z]+ [A-Z][a-z]+)/);
                                const name = nameMatch ? nameMatch[1] : '';
                                
                                return {
                                    href: href,
                                    text: text.trim(),
                                    classes: classes,
                                    name: name,
                                    isEmployeeLink: href.includes('employee') || href.includes('person') || href.includes('profile')
                                };
                            }
                        """)
                        
                        if data['isEmployeeLink'] or data['name']:
                            employee_data.append({
                                "selector": selector,
                                "index": i,
                                **data
                            })
                            print(f"  ✅ Employee: {data['name']} - {data['href']}")
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"  ❌ Error with {selector}: {e}")
        
        # Save employee data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = f"{self.capture_dir}/employee_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(employee_data, f, indent=2)
        print(f"💾 Saved employee data to: {data_file}")
        
        return employee_data
    
    async def close_browser(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            print("🔒 Browser closed")

async def main():
    """Main function"""
    print("🔍 Advanced Selector Recorder")
    print("=" * 50)
    
    recorder = AdvancedSelectorRecorder()
    
    try:
        await recorder.start_browser()
        
        # Navigate and wait for content
        if not await recorder.navigate_and_wait():
            print("❌ Failed to navigate to page")
            return
        
        # Analyze page structure
        page_structure = await recorder.analyze_page_structure()
        
        # Test selectors
        selector_results = await recorder.test_employee_selectors(page_structure)
        
        # Find best selectors
        best_selectors = [sel for sel, data in selector_results.items() 
                         if data.get("found") and data.get("count", 0) > 0]
        
        print(f"\n🎯 Best selectors found: {len(best_selectors)}")
        for sel in best_selectors[:10]:  # Show top 10
            count = selector_results[sel]["count"]
            print(f"   {sel} ({count} elements)")
        
        # Capture employee data
        if best_selectors:
            employee_data = await recorder.capture_employee_data(best_selectors)
            print(f"\n📊 Captured {len(employee_data)} employee records")
        else:
            print("\n❌ No suitable selectors found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await recorder.close_browser()

if __name__ == "__main__":
    asyncio.run(main())
