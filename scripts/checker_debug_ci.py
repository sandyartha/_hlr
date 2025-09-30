from playwright.sync_api import sync_playwright
import time
import os
import random
import logging

def random_delay():
    time.sleep(random.uniform(1, 3))

def scrape_hlr():
    print("Starting HLR scraping with Playwright...")
    
    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-blink-features=AutomationControlledFeatures'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Create page with longer default timeout
            page = context.new_page()
            page.set_default_timeout(60000)  # 60 seconds default timeout
            
            try:
                # Navigate to the page
                print("Navigating to page...")
                page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html", timeout=60000)
                
                # Wait for key elements to load instead of full network idle
                print("Waiting for page load...")
                try:
                    # First wait for basic load state
                    page.wait_for_load_state("domcontentloaded", timeout=30000)
                    
                    # Then wait for specific elements that indicate the page is usable
                    page.wait_for_selector('.content-wrapper', timeout=30000)
                    
                except Exception as timeout_error:
                    print("Warning: Timeout while waiting for some elements, continuing anyway...")
                    
                # Handle Cloudflare if needed
                max_retries = 5
                retry_count = 0
                
                while retry_count < max_retries:
                    title = page.title()
                    print(f"Page title: {title}")
                    
                    if "Just a moment" not in title:
                        break
                        
                    print(f"Cloudflare detected, waiting... (attempt {retry_count + 1}/{max_retries})")
                    random_delay()
                    retry_count += 1
                
                # Save debugging info
                content = page.content()
                print(f"Page content length: {len(content)} bytes")
                print("Saving debug info...")
                
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                
                page.screenshot(path="debug_screenshot.png")
                
                return {
                    "title": title,
                    "url": page.url,
                    "success": "Just a moment" not in title
                }
                
            finally:
                context.close()
                browser.close()
                
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the scraper
    results = scrape_hlr()
    
    # Check results
    if results.get("success"):
        print("\nScraping successful!")
        print(f"Page title: {results.get('title')}")
        print(f"URL: {results.get('url')}")
    else:
        print("\nScraping failed!")
        if "error" in results:
            print(f"Error: {results['error']}")
        print("See debug.html and debug_screenshot.png for more information")



