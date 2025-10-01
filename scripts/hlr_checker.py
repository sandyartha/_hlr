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

def random_delay(min_seconds=1, max_seconds=3):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Add stealth headers
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    return webdriver.Chrome(options=chrome_options)

def scrape_hlr():
    print("Starting HLR scraping with Botasaurus...")
    
    try:
        # Visit the website
        print("Navigating to page...")
        driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html")
        
        # Wait for key elements with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to find content...")
                
                # Wait for content to be visible
                driver.scroll_to_bottom()
                random_delay(3, 5)
                
                # Try to get the title
                title = driver.get_text("section.content-header h1")
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
        
        # Take screenshot for verification
        os.makedirs("debug", exist_ok=True)
        driver.save_screenshot("debug/debug_screenshot.png")
        
        # Save page source
        html_content = driver.page_source
        with open("debug/debug.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return {
            "title": title,
            "url": driver.current_url,
            "success": True
        }
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        
        # Save debug info even on failure
        try:
            os.makedirs("debug", exist_ok=True)
            driver.save_screenshot("debug/error_screenshot.png")
            with open("debug/error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except:
            print("Could not save debug info")
            
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
        print("See debug/debug.html and debug/debug_screenshot.png for more information")