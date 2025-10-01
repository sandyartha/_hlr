from botasaurus_driver import Driver
import time
import random
import logging
import os

def setup_driver():
    """Setup Driver with cloudflare bypass"""
    return Driver()

def handle_cloudflare(driver, max_wait=60):
    """Handle Cloudflare detection intelligently"""
    print("Checking for Cloudflare...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if "Just a moment" in driver.title:
            print("Detected Cloudflare challenge, waiting...")
            # Use built-in waits
            driver.smart_sleep(5)
            continue
            
        if driver.exists("section.content-header"):
            print("Cloudflare challenge passed!")
            return True
            
    return False

def save_debug_info(driver, prefix="debug"):
    """Save debug information with enhanced features"""
    print(f"Saving {prefix} information...")
    try:
        os.makedirs("debug", exist_ok=True)
        
        # Take full page screenshot
        screenshot_path = f"debug/{prefix}_screenshot.png"
        driver.save_full_screenshot(screenshot_path)
        print(f"Full page screenshot saved to {screenshot_path}")
        
        # Save page source with formatting
        html_path = f"debug/{prefix}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.get_formatted_page_source())
        print(f"Formatted page source saved to {html_path}")
        
        # Save extra debug info
        debug_info = {
            "url": driver.current_url,
            "title": driver.title,
            "cookies": driver.get_cookies(),
            "local_storage": driver.get_local_storage(),
            "session_storage": driver.get_session_storage()
        }
        
        with open(f"debug/{prefix}_info.txt", "w", encoding="utf-8") as f:
            for key, value in debug_info.items():
                f.write(f"{key}:\n{value}\n\n")
        
    except Exception as e:
        print(f"Error saving debug info: {str(e)}")

def scrape_hlr():
    print("\nStarting HLR scraping with enhanced Botasaurus Driver...")
    driver = None
    
    try:
        # Initialize driver with advanced settings
        driver = setup_driver()
        print("Browser initialized with enhanced features")
        
        # Visit the website with cloudflare bypass
        print("Navigating to page...")
        driver.google_get("https://ceebydith.com/cek-hlr-lokasi-hp.html", bypass_cloudflare=True)
        print("Page loaded with Cloudflare bypass")
            
        # Wait for key elements with enhanced retry mechanism
        max_retries = 3
        title = None
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to find content...")
                
                # Wait for content with auto-retry
                header = driver.wait_for_selector("section.content-header h1", timeout=20)
                
                # Smart scroll with wait
                driver.scroll_smooth()
                driver.smart_sleep(2)
                
                # Get title with validation
                title = header.text
                if title and "HLR" in title:
                    print(f"Successfully found title: {title}")
                    break
                    
                print("Title not found yet, retrying...")
                driver.smart_sleep(3)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    driver.refresh()
                    driver.smart_sleep(3)
                    continue
                raise
        
        # Save comprehensive debug info
        save_debug_info(driver)
        
        return {
            "title": title,
            "url": driver.current_url,
            "success": True,
            "cookies": driver.get_cookies()
        }
        
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        
        # Save comprehensive error debug info
        if driver:
            save_debug_info(driver, "error")
            
        return {
            "error": str(e),
            "success": False
        }
    
    finally:
        if driver:
            try:
                print("Closing browser...")
                driver.quit()
                print("Browser closed successfully")
            except Exception as close_error:
                print(f"Error closing browser: {str(close_error)}")

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
        print(f"Cookies captured: {len(results.get('cookies', []))}")
    else:
        print("\nScraping failed!")
        if "error" in results:
            print(f"Error: {results['error']}")
        print("See debug folder for detailed information")