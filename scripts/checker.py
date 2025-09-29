import asyncio
import datetime
import pandas as pd
import random
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://ceebydith.com/cek-hlr-lokasi-hp.html"
RAW_DIR = Path("raw")
OUT_DIR = Path("raw_checker")

# Ensure directories exist
RAW_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)


async def check_number(page, msisdn: str) -> dict:
    """Cek 1 nomor di halaman HLR lookup dengan bypass disabled"""
    for attempt in range(2):
        try:
            # Hard reload page untuk menghindari cache
            await page.goto("about:blank")
            await page.wait_for_timeout(500)
            
            # Navigate ke halaman dengan pendekatan yang lebih sederhana
            await page.goto(URL, wait_until="commit", timeout=10000)
            
            # Tunggu dan cek form dengan lebih agresif
            for _ in range(3):
                try:
                    # Coba enable form dengan JavaScript
                    await page.evaluate("""() => {
                        function enableElement(selector) {
                            const el = document.querySelector(selector);
                            if (el) {
                                el.disabled = false;
                                el.removeAttribute('disabled');
                                return true;
                            }
                            return false;
                        }
                        return enableElement('#msisdn') && enableElement('#find');
                    }""")
                    
                    # Cek apakah form sudah bisa digunakan
                    input_visible = await page.wait_for_selector("#msisdn", 
                        state="visible", timeout=3000)
                    button_visible = await page.wait_for_selector("#find", 
                        state="visible", timeout=3000)
                        
                    if input_visible and button_visible:
                        break
                except:
                    await page.reload(wait_until="commit")
                    await page.wait_for_timeout(1000)
            
            # Fill dan submit form
            await page.evaluate('(msisdn) => document.querySelector("#msisdn").value = msisdn', msisdn)
            await page.click("#find")

            # Tunggu dan ambil hasil dengan retry
            result_text = None
            for _ in range(3):
                try:
                    # Tunggu message muncul
                    await page.wait_for_selector("pre.message", timeout=5000)
                    
                    # Tunggu konten berubah
                    await page.wait_for_function("""
                        () => {
                            const el = document.querySelector('pre.message');
                            return el && el.innerText && 
                                (el.innerText.includes('Operator') || 
                                 el.innerText.includes('ERROR'));
                        }
                    """, timeout=5000)
                    
                    result_text = await page.eval_on_selector(
                        "pre.message", 
                        "el => el.innerText"
                    )
                    
                    if result_text and result_text.strip():
                        break
                        
                except Exception as e:
                    print(f"⚠️ Menunggu hasil... retry")
                    await page.wait_for_timeout(1000)
            
            if not result_text:
                raise Exception("Tidak ada respon dari server")

            # parsing hasil
            provider, hlr = None, None
            for line in result_text.splitlines():
                if "Operator" in line:
                    provider = line.split(":", 1)[1].strip()
                elif "HLR" in line:
                    hlr = line.split(":", 1)[1].strip()

            return {"provider": provider, "hlr": hlr, "raw_text": result_text}

        except Exception as e:
            print(f"⚠️ Gagal cek {msisdn} (attempt {attempt+1}): {e}")
            await asyncio.sleep(5)

    # kalau gagal 3x
    return {"provider": None, "hlr": None, "raw_text": ""}



async def process_file(playwright, filepath: Path):
    """Proses 1 file CSV"""
    outpath = OUT_DIR / filepath.name
    if outpath.exists():
        print(f"⏭️  Skip {filepath.name}, hasil sudah ada")
        return

    start_time = datetime.datetime.now()
    print(f"🔎 Processing {filepath.name} at {start_time.strftime('%H:%M:%S')}")
    df = pd.read_csv(filepath)

    if "prefix" not in df.columns:
        print(f"⚠️ File {filepath.name} tidak ada kolom 'prefix'")
        return

    results = []
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '--disable-notifications',
            '--disable-extensions',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-component-extensions-with-background-pages',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            '--disable-ipc-flooding-protection',
            '--disable-default-apps'
        ]
    )
    context = await browser.new_context(
        viewport={'width': 800, 'height': 600},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        bypass_csp=True,
        ignore_https_errors=True
    )
    page = await context.new_page()
    
    # Set default timeout untuk semua operasi
    page.set_default_timeout(10000)
    
    # Aktifkan intercept request
    await page.route('**/*', lambda route: route.continue_() if route.request.resource_type in ['document', 'script'] else route.abort())

    for idx, row in df.iterrows():
        prefix = str(row["prefix"])

        # generate nomor acak biar lebih realistis
        msisdn = "0" + prefix + "".join(str(random.randint(0, 9)) for _ in range(7))

        print(f"🔄 Cek prefix {prefix} → {msisdn}")

        try:
            res = await check_number(page, msisdn)
        except Exception as e:
            print(f"⚠️ Error fatal saat cek {prefix}: {e}")
            res = {"provider": None, "hlr": None, "raw_text": ""}

        results.append({
            "prefix": prefix,
            "city_csv": row.get("city", ""),
            "sim_csv": row.get("sim_card", ""),
            "provider_csv": row.get("provider", ""),
            "provider_api": res["provider"],
            "hlr_api": res["hlr"],
            "raw_text": res["raw_text"],
        })

        # simpan partial setiap 10 baris biar tidak hilang kalau crash
        if (idx + 1) % 10 == 0:
            pd.DataFrame(results).to_csv(outpath, index=False)
            print(f"💾 Progress disimpan sementara ({idx+1} rows)")

        await asyncio.sleep(1)  # kurangi delay ke 1 detik

    await browser.close()

    outdf = pd.DataFrame(results)
    outdf.to_csv(outpath, index=False)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✅ Hasil disimpan: {outpath} ({len(results)} records)")
    print(f"⏱️ Total waktu proses: {duration:.1f} detik ({duration/len(results):.1f} detik per record)")


async def main():
    # Get list of all CSV files
    csv_files = list(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in raw directory!")
        return

    # Select one file based on current minute
    current_minute = int(datetime.datetime.now().minute)
    selected_file = csv_files[current_minute % len(csv_files)]
    
    print(f"🎯 Selected file for this run: {selected_file.name}")
    
    async with async_playwright() as p:
        await process_file(p, selected_file)


if __name__ == "__main__":
    import datetime
    asyncio.run(main())

# ggggg