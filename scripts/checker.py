import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright

RAW_DIR = "raw"
OUT_DIR = "raw_checker"
URL = "https://contoh-hlr-lookup.com"  # ganti dengan URL asli

async def check_number(page, nomor: str) -> str | None:
    """Cek nomor HLR pada website target."""
    try:
        # Aktifkan input & button dulu
        await page.evaluate("""
            document.getElementById('msisdn')?.removeAttribute('disabled');
            document.getElementById('find')?.removeAttribute('disabled');
        """)

        # Clear dulu input biar tidak menumpuk
        await page.fill('#msisdn', '')
        # Isi nomor
        await page.fill('#msisdn', nomor)

        # Klik cari
        await page.click('#find')

        # Tunggu hasil (selector bisa disesuaikan)
        await page.wait_for_selector('.hasil, #result, table', timeout=7000)

        hasil = await page.inner_text('.hasil, #result, table')
        return hasil.strip()
    except Exception as e:
        print(f"⚠️ Gagal memproses {nomor}: {e}")
        return None


async def process_file(playwright, filepath: str):
    """Proses satu file CSV berisi daftar nomor"""
    filename = os.path.basename(filepath)
    outpath = os.path.join(OUT_DIR, filename)

    # Jika sudah ada hasilnya, skip
    if os.path.exists(outpath):
        print(f"⏭️  Skip {filename}, sudah ada hasil.")
        return

    print(f"🔎 Processing {filename}")

    # Load data CSV
    try:
        df = pd.read_csv(filepath, dtype=str)
    except Exception as e:
        print(f"⚠️ Gagal baca {filename}: {e}")
        return

    # Pastikan ada kolom 'msisdn'
    if "msisdn" not in df.columns:
        print(f"⚠️ File {filename} tidak ada kolom 'msisdn'")
        return

    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(URL, timeout=60000)

    results = []
    for nomor in df["msisdn"].dropna():
        nomor = nomor.strip()
        if not nomor:
            continue
        hasil = await check_number(page, nomor)
        results.append({"msisdn": nomor, "result": hasil})

    await browser.close()

    # Simpan hasil
    out_df = pd.DataFrame(results)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_df.to_csv(outpath, index=False)
    print(f"✅ Hasil disimpan: {outpath}")


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        for file in os.listdir(RAW_DIR):
            if file.endswith(".csv"):
                filepath = os.path.join(RAW_DIR, file)
                await process_file(p, filepath)


if __name__ == "__main__":
    asyncio.run(main())
