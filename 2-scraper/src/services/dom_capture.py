#!/usr/bin/env python3
"""
DOM Capture and Selector Recorder
Captures the DOM structure of the employee directory page to find correct selectors
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from .auth import AutoLogin


class DOMCapture:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        # Set correct path to debug directory (3 levels up from services)
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        self.capture_dir = str(project_root / "debug" / "dom_captures")
        
    async def start_browser(self):
        """Start browser and navigate to employee directory"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            slow_mo=1000     # Slow down for observation
        )
        self.page = await self.browser.new_page()
        
        # Set viewport
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
        print("🌐 Navigating to employee directory...")
        await self.page.goto("https://ei.ennead.com/employees/1/all-employees", wait_until="networkidle")
        
        # Check if authentication is required and use AutoLogin
        current_url = self.page.url
        page_title = await self.page.title()
        
        login_indicators = [
            "sign in", "login", "authentication", "microsoft", "oauth",
            "password", "username", "account"
        ]
        
        is_login_page = any(indicator in page_title.lower() or indicator in current_url.lower() 
                          for indicator in login_indicators)
        
        if is_login_page:
            print("🔐 Authentication required - using AutoLogin...")
            try:
                auth = AutoLogin(self.page)
                await auth.login()
                print("✅ AutoLogin successful!")
            except Exception as e:
                print(f"❌ AutoLogin failed: {e}")
                print("   Falling back to manual login...")
                print("   Press Enter after logging in to continue...")
                input()
        
    async def capture_dom_structure(self):
        """Capture DOM structure and analyze selectors"""
        print("📸 Capturing DOM structure...")
        
        # Wait for page to load
        await self.page.wait_for_timeout(3000)
        
        # Capture full page HTML
        html_content = await self.page.content()
        
        # Save full HTML
        os.makedirs(self.capture_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = f"{self.capture_dir}/employee_directory_{timestamp}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Saved full HTML to: {html_file}")
        
        # Analyze potential employee selectors
        selectors_to_test = [
            # Common employee card selectors
            ".employee-card",
            ".person-card", 
            ".employee-item",
            ".person-item",
            ".staff-card",
            ".team-member",
            "[data-employee]",
            "[data-person]",
            ".card",
            ".profile-card",
            
            # List item selectors
            "li",
            ".list-item",
            ".directory-item",
            
            # Link selectors
            "a[href*='employee']",
            "a[href*='person']",
            "a[href*='profile']",
            
            # Generic content selectors
            ".content",
            ".main-content",
            ".directory",
            ".employee-list",
            ".staff-list"
        ]
        
        selector_results = {}
        
        for selector in selectors_to_test:
            try:
                elements = await self.page.query_selector_all(selector)
                count = len(elements)
                selector_results[selector] = {
                    "count": count,
                    "found": count > 0
                }
                
                if count > 0:
                    print(f"✅ {selector}: {count} elements found")
                    
                    # Get sample element info
                    if count > 0:
                        sample_element = elements[0]
                        tag_name = await sample_element.evaluate("el => el.tagName")
                        class_name = await sample_element.get_attribute("class") or ""
                        href = await sample_element.get_attribute("href") or ""
                        
                        selector_results[selector]["sample"] = {
                            "tag": tag_name,
                            "class": class_name,
                            "href": href[:100] if href else ""
                        }
                else:
                    print(f"❌ {selector}: No elements found")
                    
            except Exception as e:
                selector_results[selector] = {
                    "count": 0,
                    "found": False,
                    "error": str(e)
                }
                print(f"⚠️ {selector}: Error - {e}")
        
        # Save selector analysis
        analysis_file = f"{self.capture_dir}/selector_analysis_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(selector_results, f, indent=2)
        print(f"📊 Saved selector analysis to: {analysis_file}")
        
        # Find the best selector
        best_selectors = [sel for sel, data in selector_results.items() 
                         if data.get("found") and data.get("count", 0) > 0]
        
        if best_selectors:
            print(f"\n🎯 Best selectors found:")
            for sel in best_selectors:
                count = selector_results[sel]["count"]
                print(f"   {sel} ({count} elements)")
        else:
            print("\n❌ No suitable selectors found")
            
        return selector_results, best_selectors
    
    async def capture_employee_links(self, best_selectors):
        """Capture actual employee links using best selectors"""
        print(f"\n🔗 Capturing employee links using best selectors...")
        
        employee_links = []
        
        for selector in best_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"Testing {selector}: {len(elements)} elements")
                
                for i, element in enumerate(elements[:10]):  # Test first 10
                    try:
                        # Check if it's a link
                        href = await element.get_attribute("href")
                        if href and "employee" in href.lower():
                            text = await element.inner_text()
                            employee_links.append({
                                "selector": selector,
                                "href": href,
                                "text": text.strip()[:50],
                                "index": i
                            })
                            print(f"  ✅ Found employee link: {text.strip()[:30]}...")
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"  ❌ Error with {selector}: {e}")
        
        # Save employee links
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        links_file = f"{self.capture_dir}/employee_links_{timestamp}.json"
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(employee_links, f, indent=2)
        print(f"💾 Saved employee links to: {links_file}")
        
        return employee_links
    
    async def close_browser(self):
        """Close browser and playwright"""
        if self.browser:
            await self.browser.close()
            print("🔒 Browser closed")
        if self.playwright:
            await self.playwright.stop()
            print("🔒 Playwright stopped")


async def main():
    """Main function"""
    print("🔍 DOM Capture and Selector Recorder")
    print("=" * 50)
    
    capture = DOMCapture()
    
    try:
        await capture.start_browser()
        selector_results, best_selectors = await capture.capture_dom_structure()
        employee_links = await capture.capture_employee_links(best_selectors)
        
        print(f"\n📋 Summary:")
        print(f"   Total selectors tested: {len(selector_results)}")
        print(f"   Working selectors: {len(best_selectors)}")
        print(f"   Employee links found: {len(employee_links)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await capture.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
