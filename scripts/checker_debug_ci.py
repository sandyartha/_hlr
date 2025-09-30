from playwright.sync_api import sync_playwright
import time
import os
import random
import logging

def random_delay(min_seconds=1, max_seconds=3):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def scrape_hlr():
    print("Starting HLR scraping with Playwright...")
    
    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-blink-features=AutomationControlledFeatures',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080'
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
                    
                # Handle Cloudflare and title extraction with better error handling
                max_retries = 5
                retry_count = 0
                title = None
                
                while retry_count < max_retries:
                    try:
                        # Try multiple methods to get the title
                        title = page.evaluate('() => document.title')
                        print(f"Title from evaluate: {title}")
                        
                        if not title:
                            title = page.evaluate('() => document.querySelector("title")?.textContent')
                            print(f"Title from querySelector: {title}")
                            
                        if not title:
                            h1_text = page.evaluate('() => document.querySelector("h1")?.textContent')
                            print(f"H1 text found: {h1_text}")
                            title = h1_text if h1_text else "Unknown Title"
                            
                        print(f"Final page title: {title}")
                        
                        if title and "Just a moment" not in title:
                            break
                            
                        # Check for Cloudflare
                        cloudflare_elements = page.query_selector_all('text="Checking if the site connection is secure"')
                        if len(cloudflare_elements) > 0:
                            print(f"Cloudflare challenge detected (attempt {retry_count + 1}/{max_retries})")
                            random_delay()
                            page.reload()
                        else:
                            break
                            
                    except Exception as e:
                        print(f"Error getting title (attempt {retry_count + 1}): {str(e)}")
                        
                    retry_count += 1
                    random_delay()
                
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



