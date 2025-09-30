import asyncio
from undetected_playwright.async_api import async_playwright
import time

async def scrape_basic_info():
    """Scrape title dan description dari halaman web"""
    try:
        async with async_playwright() as p:
            print("Launching browser dengan undetected mode...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-blink-features=AutomationControlledFeatures'
                ]
            )
            
            # Buat context dan page
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            print("Membuka halaman...")
            await page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html", timeout=60000)
            
            print("Menunggu halaman selesai loading...")
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Get page title
            title = await page.title()
            print(f"Title: {title}")
            
            # Handle Cloudflare if needed
            if "Just a moment" in title:
                print("Terdeteksi Cloudflare challenge, menunggu...")
                await asyncio.sleep(10)
                title = await page.title()
                print(f"Title setelah menunggu: {title}")
            
            # Get meta description
            description = await page.evaluate("""() => {
                const meta = document.querySelector('meta[name="description"]');
                return meta ? meta.getAttribute('content') : '';
            }""")
            print(f"Description: {description}")
            
            # Save halaman untuk debug
            content = await page.content()
            print(f"\nPage content length: {len(content)} bytes")
            print("Saving page content to debug.html...")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Take screenshot
            await page.screenshot(path="debug_screenshot.png")
            
            await context.close()
            await browser.close()
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(scrape_basic_info())