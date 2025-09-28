import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

RAW_DIR = Path("raw")
OUT_DIR = Path("raw_checker")
OUT_DIR.mkdir(exist_ok=True)

def process_file(csv_file, page):
    print(f"▶️ Processing {csv_file.name}")
    df = pd.read_csv(csv_file)
    results = []

    for _, row in df.iterrows():
        prefix = str(row["prefix"])
        msisdn = "0" + prefix + "0000000"

        page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html")

        # Tutup alert kalau ada
        try:
            page.click(".alert .close", timeout=3000)
        except:
            pass

        # Pastikan input aktif
        try:
            page.wait_for_selector("#msisdn", timeout=10000)
            page.locator("#msisdn").evaluate("el => el.removeAttribute('disabled')")
            page.fill("#msisdn", msisdn)
            page.click("#find")
        except Exception:
            print(f"⚠️ Gagal menemukan input #msisdn untuk {msisdn}")
            continue

        try:
            page.wait_for_function(
                """() => {
                    const el = document.querySelector("pre.message");
                    if (!el) return false;
                    const txt = el.innerText;
                    return txt.includes("Operator") || txt.includes("ERROR");
                }""", timeout=10000
            )
            text = page.inner_text("pre.message")
        except Exception:
            print(f"⚠️ Tidak ada hasil untuk {msisdn}")
            continue

        provider, hlr = None, None
        for line in text.splitlines():
            if "Operator" in line:
                provider = line.split(":", 1)[1].strip()
            elif "HLR" in line:
                hlr = line.split(":", 1)[1].strip()

        results.append({
            "prefix": prefix,
            "city_csv": row.get("city"),
            "sim_csv": row.get("sim_card"),
            "provider_csv": row.get("provider"),
            "provider_api": provider,
            "hlr_api": hlr,
            "raw_text": text
        })

        time.sleep(2)

    if results:
        out = pd.DataFrame(results)
        out_file = OUT_DIR / csv_file.name
        out.to_csv(out_file, index=False)
        print(f"✅ Saved: {out_file}")
    else:
        print(f"⚠️ No results for {csv_file.name}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for csv_file in RAW_DIR.glob("*.csv"):
            out_file = OUT_DIR / csv_file.name
            if out_file.exists():
                print(f"⏭️ Skip {csv_file.name}, already checked")
                continue
            process_file(csv_file, page)

        browser.close()

if __name__ == "__main__":
    main()
