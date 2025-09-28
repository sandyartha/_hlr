import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright

RAW_DIR = "raw"
OUT_DIR = "raw_checker"
URL = "https://ceebydith.com/cek-hlr-lokasi-hp.html"  # target website

async def check_number(page, nomor: str) -> dict:
    """Cek 1 nomor ke halaman HLR lookup dan ambil hasil"""
    try:
        # aktifkan input & tombol (karena disabled di HTML awal)
        await page.evaluate("""
            document.getElementById('msisdn')?.removeAttribute('disabled');
            document.getElementById('find')?.removeAttribute('disabled');
        """)

        # isi nomor
        await page.fill('#msisdn', '')
        await page.fill('#msisdn', nomor)

        # klik tombol
        await page.click('#find')

        # tunggu hasil keluar
        await page.wait_for_function(
            """() => {
                const el = document.querySelector("pre.message");
                if (!el) return false;
                const txt = el.innerText;
                return txt.includes("Operator") || txt.includes("ERROR");
            }""",
            timeout=10000
        )

        text = await page.inner_text("pre.message")

        provider, hlr = None, None
        for line in text.splitlines():
            if "Operator" in line:
                provider = line.split(":", 1)[1].strip()
            elif "HLR" in line:
                hlr = line.split(":", 1)[1].strip()

        return {
            "msisdn": nomor,
            "provider_api": provider,
            "hlr_api": hlr,
            "raw_text": text
        }

    except Exception as e:
        print(f"⚠️ Gagal cek {nomor}: {e}")
        return {
            "msisdn": nomor,
            "provider_api": None,
            "hlr_api": None,
            "raw_text": None
        }

async def process_file(playwright, filepath: str):
    """Proses 1 file CSV"""
    filename = os.path.basename(filepath)
    outpath = os.path.join(OUT_DIR, filename)

    # skip kalau sudah ada hasil
    if os.path.exists(outpath):
        print(f"⏭️ Skip {filename}, sudah ada hasil.")
        return

    print(f"🔎 Processing {filename}")

    try:
        # coba baca dengan header
        df = pd.read_csv(filepath, dtype=str)
        if "msisdn" in df.columns:
            numbers = df["msisdn"].dropna().tolist()
        else:
            # fallback kalau tidak ada header
            df = pd.read_csv(filepath, header=None, dtype=str)
            numbers = df.iloc[:, 0].dropna().tolist()
    except Exception as e:
        print(f"⚠️ Gagal baca {filename}: {e}")
        return

    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(URL, timeout=60000)

    results = []
    for nomor in numbers:
        nomor = str(nomor).strip()
        if not nomor:
            continue
        hasil = await check_number(page, nomor)
        results.append(hasil)

    await browser.close()

    # simpan hasil
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
