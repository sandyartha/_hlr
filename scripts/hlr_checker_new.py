from botasaurus.browser import browser, Driver

@browser
def scrape_heading_task(driver: Driver, data):
    # Visit the Omkar Cloud website
    driver.get("https://ceebydith.com/cek-hlr-lokasi-hp.html")
    
    # Retrieve the heading element's text
    heading = driver.get_text("h1")

    # Save the data as a JSON file in output/scrape_heading_task.json
    return {
        "heading": heading
    }
     
# Initiate the web scraping task
scrape_heading_task()