from botasaurus_driver import create_driver, AntiDetectDriver
import time
import random
import logging
import os

def random_delay(min_seconds=1, max_seconds=3):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def scrape_hlr():
    print("Starting HLR scraping with Botasaurus Driver...")
    driver = None
    
    try:
        # Initialize driver with anti-detection
        driver = create_driver(
            headless=True,
            window_size=(1920, 1080)
        )
        print("Browser initialized successfully")
        
        # Visit the website
        print("Navigating to page...")
        driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html")
        print("Page loaded")
        
        # Wait for key elements with retry
        max_retries = 3
        title = None
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to find content...")
                
                # Wait for content to be visible
                header = driver.wait_for_presence("section.content-header h1", timeout=20)
                
                # Scroll and wait
                driver.scroll_to_bottom()
                random_delay(3, 5)
                
                # Try to get the title
                title = header.text
                if title and "HLR" in title:
                    print(f"Successfully found title: {title}")
                    break
                    
                print("Title not found yet, waiting...")
                random_delay(5, 8)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    random_delay(5, 8)
                    continue
                raise
        
        # Create debug directory
        os.makedirs("debug", exist_ok=True)
        
        # Take screenshot for verification
        print("Taking screenshot...")
        screenshot_path = "debug/debug_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save page source
        print("Saving page source...")
        html_path = "debug/debug.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Page source saved to {html_path}")
        
        return {
            "title": title,
            "url": driver.current_url,
            "success": True
        }
        
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        
        # Save debug info even on failure
        if driver:
            try:
                os.makedirs("debug", exist_ok=True)
                print("Taking error screenshot...")
                driver.save_screenshot("debug/error_screenshot.png")
                print("Saving error page source...")
                with open("debug/error.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception as debug_error:
                print(f"Could not save debug info: {str(debug_error)}")
                
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
    else:
        print("\nScraping failed!")
        if "error" in results:
            print(f"Error: {results['error']}")
        print("See debug/debug.html and debug/debug_screenshot.png for more information")