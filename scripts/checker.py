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
    for attempt in range(3):
        try:
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            # paksa enable input & tombol
            await page.evaluate("""
                document.querySelector('#msisdn')?.removeAttribute('disabled');
                document.querySelector('#find')?.removeAttribute('disabled');
            """)

            # isi nomor & klik
            await page.fill("#msisdn", msisdn)
            await page.click("#find")

            # tunggu hasil keluar
            await page.wait_for_function(
                """() => {
                    const el = document.querySelector("pre.message");
                    if (!el) return false;
                    const txt = el.innerText;
                    return txt.includes("Operator") || txt.includes("ERROR");
                }""",
                timeout=30000
            )
            text = await page.inner_text("pre.message")

            # parsing hasil
            provider, hlr = None, None
            for line in text.splitlines():
                if "Operator" in line:
                    provider = line.split(":", 1)[1].strip()
                elif "HLR" in line:
                    hlr = line.split(":", 1)[1].strip()

            return {"provider": provider, "hlr": hlr, "raw_text": text}

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

    print(f"🔎 Processing {filepath.name}")
    df = pd.read_csv(filepath)

    if "prefix" not in df.columns:
        print(f"⚠️ File {filepath.name} tidak ada kolom 'prefix'")
        return

    results = []
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()

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

        await asyncio.sleep(2)  # delay biar ga ke-block

    await browser.close()

    outdf = pd.DataFrame(results)
    outdf.to_csv(outpath, index=False)
    print(f"✅ Hasil disimpan: {outpath}")


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