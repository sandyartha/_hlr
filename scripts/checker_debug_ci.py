from playwright.sync_api import sync_playwright
import time
import os
import random
import logging

def random_delay(min_seconds=1, max_seconds=3):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)
    
def wait_for_cloudflare_to_clear(page, max_wait=60):
    """Wait for Cloudflare challenge to be completed."""
    print(f"Waiting up to {max_wait} seconds for Cloudflare to clear...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            if "Just a moment" not in page.title():
                print("Cloudflare challenge appears to be cleared!")
                return True
                
            if page.query_selector('.content-wrapper'):
                print("Found content wrapper - page seems to be loaded!")
                return True
                
            print("Still waiting for Cloudflare...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error while checking Cloudflare status: {str(e)}")
            time.sleep(2)
            
    print("Cloudflare wait timed out")
    return False

def scrape_hlr():
    print("Starting HLR scraping with Playwright...")
    
    # Set a custom user agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    
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
                    '--window-size=1920,1080',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            
            # Inject stealth script
            js_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=user_agent,
                java_script_enabled=True,
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Ch-Ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )
            
            # Create page with longer default timeout
            page = context.new_page()
            page.set_default_timeout(60000)  # 60 seconds default timeout
            
            try:
                # Navigate to the page
                # Add stealth before navigation
                page.add_init_script(js_script)
                
                print("Navigating to page...")
                page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html", timeout=60000)
                
                # Wait longer for initial page load
                print("Waiting for initial page load...")
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                
                # Add additional wait time for Cloudflare
                print("Waiting for potential Cloudflare challenge...")
                random_delay(10, 15)  # Longer initial wait
                
                try:
                    # Check if we're still on Cloudflare
                    if "Just a moment" in page.title():
                        print("Still on Cloudflare, waiting longer...")
                        random_delay(15, 20)  # Even longer wait if still on Cloudflare
                    
                    # Then wait for specific elements that indicate the page is usable
                    page.wait_for_selector('.content-wrapper', timeout=30000)
                    
                except Exception as timeout_error:
                    print("Warning: Timeout while waiting for some elements, continuing anyway...")
                    
                # Handle Cloudflare and title extraction with better error handling
                max_retries = 3  # Reduced retries but with longer waits
                retry_count = 0
                title = None
                
                # Try to wait for Cloudflare to clear first
                if wait_for_cloudflare_to_clear(page, max_wait=60):
                    print("Successfully waited for Cloudflare!")
                else:
                    print("Warning: Could not confirm Cloudflare clearance")
                
                while retry_count < max_retries:
                    try:
                        print(f"\nAttempt {retry_count + 1}/{max_retries} to bypass Cloudflare...")
                        
                        # Wait for Cloudflare challenge to complete
                        try:
                            # First check if we're on Cloudflare page
                            if page.query_selector('div[class*="cf-"]') is not None:
                                print("Detected Cloudflare challenge page, waiting for completion...")
                                # Wait longer for the first attempt
                                wait_time = 20 if retry_count == 0 else 10
                                random_delay(wait_time, wait_time + 5)
                                
                                # Wait for the main content to appear
                                page.wait_for_selector('.content-wrapper', timeout=30000)
                            else:
                                print("No Cloudflare challenge detected")
                        except Exception as cf_error:
                            print(f"Error during Cloudflare check: {str(cf_error)}")
                        
                        # Try multiple methods to get the title
                        try:
                            title = page.evaluate('() => document.title')
                            print(f"Title from evaluate: {title}")
                        except:
                            print("Failed to get title via evaluate")
                            
                        if not title or "Just a moment" in title:
                            try:
                                # Try to find the main content heading
                                heading = page.evaluate('''() => {
                                    const h1 = document.querySelector('.content-header h1');
                                    return h1 ? h1.textContent : null;
                                }''')
                                if heading:
                                    title = heading
                                    print(f"Got title from heading: {title}")
                            except:
                                print("Failed to get heading")
                            
                        print(f"Current page title: {title}")
                        
                        if title and "Just a moment" not in title:
                            print("Successfully bypassed Cloudflare!")
                            break
                            
                        # If still on Cloudflare page, try reloading
                        print("Still on Cloudflare page, reloading...")
                        page.reload()
                        random_delay(5, 8)  # Longer delay between reloads
                            
                    except Exception as e:
                        print(f"Error during attempt {retry_count + 1}: {str(e)}")
                        
                    retry_count += 1
                
                # Take screenshot first to ensure page is rendered
                print("Taking screenshot...")
                page.screenshot(path="debug_screenshot.png")
                
                print("Waiting after screenshot...")
                random_delay(3, 5)  # Give extra time for any dynamic content
                
                # Try to get title again after ensuring page is rendered
                try:
                    print("Attempting to get title after screenshot...")
                    # Try multiple selectors to find the title
                    title_selectors = [
                        '.content-header h1',  # Content header h1 first (most specific)
                        'section.content-header h1',  # More specific content header
                        'title',  # Page title tag
                        '.content-wrapper .content-header h1', # Full path
                        'h1',  # Direct h1 as last resort
                    ]
                    
                    for selector in title_selectors:
                        try:
                            elements = page.query_selector_all(selector)
                            for element in elements:
                                try:
                                    text = element.text_content().strip()
                                    print(f"Found text via selector '{selector}': {text}")
                                    # Check for the expected title content
                                    if text and "HLR" in text and "Lokasi HP" in text:
                                        title = text
                                        print(f"Found matching title: {title}")
                                        break
                                    elif text and not "Just a moment" in text:
                                        # Store as backup if we don't find the perfect match
                                        if not title:
                                            title = text
                                except Exception as text_error:
                                    print(f"Error getting text content: {str(text_error)}")
                            if title and "HLR" in title:
                                break  # Found the perfect match, exit the selector loop
                        except Exception as e:
                            print(f"Failed to get title from {selector}: {str(e)}")
                    
                    if not title or "Just a moment" in title:
                        # Final attempt - try to get any visible text from the content area
                        content_text = page.evaluate('''() => {
                            const content = document.querySelector('.content-wrapper');
                            return content ? content.innerText.split('\\n')[0] : null;
                        }''')
                        if content_text:
                            title = content_text
                            print(f"Got title from content: {title}")
                            
                except Exception as e:
                    print(f"Error getting title after screenshot: {str(e)}")
                
                # Save debug info
                content = page.content()
                print(f"Page content length: {len(content)} bytes")
                print("Saving debug info...")
                
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                
                success = title and "Just a moment" not in title
                print(f"Final title: {title}")
                print(f"Success: {success}")
                
                return {
                    "title": title,
                    "url": page.url,
                    "success": success
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



