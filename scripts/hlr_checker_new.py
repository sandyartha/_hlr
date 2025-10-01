from botasaurus_driver import Driver
import time
import random
import logging
import os

def save_debug_info(driver, prefix="debug"):
    """Save debug information"""
    print(f"Saving {prefix} information...")
    try:
        os.makedirs("debug", exist_ok=True)
        
        # Take screenshot
        driver.screenshot(f"debug/{prefix}_screenshot.png")
        
        # Save page source
        with open(f"debug/{prefix}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Save basic info
        with open(f"debug/{prefix}_info.txt", "w", encoding="utf-8") as f:
            f.write(f"URL: {driver.current_url}\n")
            f.write(f"Title: {driver.title}\n")
            
    except Exception as e:
        print(f"Error saving debug info: {str(e)}")

def scrape_hlr():
    """Main scraping function with automatic Cloudflare bypass"""
    print("\nStarting HLR scraping...")
    driver = None
    
    try:
        # Initialize driver
        driver = Driver()
        print("Browser initialized")
        
        # Visit website with cloudflare bypass
        print("Navigating to page...")
        driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html", bypass_cloudflare=True)
        print("Page loaded with Cloudflare bypass")
        
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
    results = scrape_hlr()
    
    # Check results
    if results and results.get("success"):
        print("\nScraping successful!")
        print(f"Page title: {results.get('title')}")
        print(f"URL: {results.get('url')}")
    else:
        print("\nScraping failed!")
        if results and "error" in results:
            print(f"Error: {results['error']}")
        print("See debug folder for detailed information")