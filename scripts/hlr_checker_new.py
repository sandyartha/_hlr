from botasaurus import bt
from botasaurus.browser import browser, Driver
import time
import random
import logging
import os

def save_debug_info(driver, prefix="debug"):
    """Save debug information"""
    print(f"Saving {prefix} information...")
    try:
        os.makedirs("debug", exist_ok=True)
        
        # Take screenshot using save_screenshot instead of screenshot
        screenshot_path = f"debug/{prefix}_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save page source
        html_path = f"debug/{prefix}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Page source saved to {html_path}")
        
        # Save basic info
        info_path = f"debug/{prefix}_info.txt"
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {driver.current_url}\n")
            f.write(f"Title: {driver.title}\n")
        print(f"Debug info saved to {info_path}")
            
    except Exception as e:
        print(f"Error saving debug info: {str(e)}")

@browser(
    block_images_and_css=True,
    wait_for_complete_page_load=True,
    parallel=1,
    reuse_driver=True,
    cache=True,
    tiny_profile=True,
    profile="hlr_checker"
)
def scrape_hlr(driver: Driver, data):
    """Main scraping function with automatic Cloudflare bypass"""
    print("\nStarting HLR scraping...")
    try:
        # Visit website with Cloudflare handling
        print("Navigating to page...")
        driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html")
        print("Page loaded")
        
        # Wait for key elements with retry
        max_retries = 3
        title = None
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to find content...")
                
                # Try multiple selectors
                for selector in ["section.content-header h1", ".content-header h1", "h1"]:
                    if driver.exists(selector):
                        title = driver.get_text(selector)
                        break
                
                if title and "HLR" in title:
                    print(f"Successfully found title: {title}")
                    break
                    
                print("Title not found yet, retrying...")
                driver.sleep(3)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    driver.refresh()
                    driver.sleep(3)
                    continue
                raise
                
        # Save debug info
        save_debug_info(driver)
        
        return {
            "title": title,
            "url": driver.current_url,
            "success": True
        }
        
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        
        # Save error debug info
        save_debug_info(driver, "error")
        
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
    print("Starting scraper...")
    results = bt.run(scrape_hlr)
    
    # Check first result
    result = results[0] if results else None
    
    if result and result.get("success"):
        print("\nScraping successful!")
        print(f"Page title: {result.get('title')}")
        print(f"URL: {result.get('url')}")
    else:
        print("\nScraping failed!")
        if result and "error" in result:
            print(f"Error: {result['error']}")
        print("See debug folder for detailed information")