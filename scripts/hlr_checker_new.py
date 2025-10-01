from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging
import os
import sys

def random_delay(min_seconds=1, max_seconds=3):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def setup_driver():
    print("Setting up Chrome driver...")
    try:
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome driver setup successful")
        return driver
        
    except Exception as e:
        print(f"Error setting up Chrome driver: {str(e)}")
        raise

def get_title_with_retry(driver, max_retries=3):
    print("Attempting to get page title...")
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to find content...")
            
            # Wait for content to be visible
            wait = WebDriverWait(driver, 20)
            header = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.content-header h1")))
            
            # Scroll and wait
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(3, 5)
            
            # Try to get the title
            title = header.text
            if title and "HLR" in title:
                print(f"Successfully found title: {title}")
                return title
                
            print("Title not found yet, waiting...")
            random_delay(5, 8)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                random_delay(5, 8)
                continue
            raise
            
    raise Exception("Could not find title after all attempts")

def save_debug_info(driver, prefix="debug"):
    print(f"Saving {prefix} information...")
    try:
        os.makedirs("debug", exist_ok=True)
        
        # Take screenshot
        screenshot_path = f"debug/{prefix}_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save page source
        html_path = f"debug/{prefix}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Page source saved to {html_path}")
            
    except Exception as e:
        print(f"Error saving debug info: {str(e)}")

def scrape_hlr():
    print("\nStarting HLR scraping with Selenium...")
    driver = None
    
    try:
        # Initialize driver
        driver = setup_driver()
        
        # Visit the website
        print("\nNavigating to page...")
        driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html")
        print("Page loaded")
        
        # Get title with retry mechanism
        title = get_title_with_retry(driver)
        
        # Save successful debug info
        save_debug_info(driver)
        
        return {
            "title": title,
            "url": driver.current_url,
            "success": True
        }
        
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        
        # Save error debug info
        if driver:
            save_debug_info(driver, "error")
            
        return {
            "error": str(e),
            "success": False
        }
    
    finally:
        if driver:
            try:
                print("\nClosing browser...")
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