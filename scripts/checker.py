import asyncio
import pandas as pd
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://ceebydith.com/cek-hlr-lokasi-hp.html"
RAW_DIR = Path("raw")
OUT_DIR = Path("raw_checker")
OUT_DIR.mkdir(exist_ok=True)

async def check_number(page, msisdn: str) -> dict:
    """Cek 1 nomor di halaman HLR lookup"""
    await page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    # tunggu input aktif
    await page.wait_for_selector("#msisdn:not([disabled])", timeout=10000)

    # isi nomor
    await page.fill("#msisdn", msisdn)

    # tunggu tombol aktif lalu klik
    await page.wait_for_selector("#find:not([disabled])", timeout=5000)
    await page.click("#find")

    # tunggu hasil
    try:
        await page.wait_for_function(
            """() => {
                const el = document.querySelector("pre.message");
                if (!el) return false;
                const txt = el.innerText;
                return txt.includes("Operator") || txt.includes("ERROR");
            }""",
            timeout=15000
        )
        text = await page.inner_text("pre.message")
    except Exception as e:
        print(f"⚠️ Timeout untuk {msisdn}")
        return {"provider": None, "hlr": None, "raw_text": ""}

    # parsing hasil
    provider, hlr = None, None
    for line in text.splitlines():
        if "Operator" in line:
            provider = line.split(":", 1)[1].strip()
        elif "HLR" in line:
            hlr = line.split(":", 1)[1].strip()

    return {"provider": provider, "hlr": hlr, "raw_text": text}


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

    for _, row in df.iterrows():
        prefix = str(row["prefix"])
        msisdn = "0" + prefix + "0000000"

        try:
            res = await check_number(page, msisdn)
        except Exception as e:
            print(f"⚠️ Gagal cek {prefix}: {e}")
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

        await asyncio.sleep(2)  # delay biar ga ke-block

    await browser.close()

    outdf = pd.DataFrame(results)
    outdf.to_csv(outpath, index=False)
    print(f"✅ Hasil disimpan: {outpath}")


async def main():
    async with async_playwright() as p:
        for filepath in RAW_DIR.glob("*.csv"):
            await process_file(p, filepath)


if __name__ == "__main__":
    asyncio.run(main())
