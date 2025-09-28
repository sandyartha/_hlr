import pandas as pd
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

RAW_DIR = Path("raw")
OUT_DIR = Path("raw_checker")
OUT_DIR.mkdir(exist_ok=True)

def process_file(path: Path, page):
    out_file = OUT_DIR / path.name
    if out_file.exists():
        print(f"✅ Skip {path.name}, already checked.")
        return

    df = pd.read_csv(path)
    results = []

    for _, row in df.iterrows():
        prefix = str(row["prefix"])
        msisdn = "0" + prefix + "0000000"

        page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html")

        # aktifkan input
        page.evaluate("document.querySelector('#msisdn').removeAttribute('disabled')")
        page.fill("#msisdn", msisdn)
        page.click("#find")

        # tunggu sampai hasil keluar
        page.wait_for_function(
            '''() => {
                const el = document.querySelector("pre.message");
                if (!el) return false;
                const txt = el.innerText;
                return txt.includes("Operator") || txt.includes("ERROR");
            }''',
            timeout=15000
        )

        text = page.inner_text("pre.message")

        provider, hlr = None, None
        for line in text.splitlines():
            if "Operator" in line:
                provider = line.split(":", 1)[1].strip()
            elif "HLR" in line:
                hlr = line.split(":", 1)[1].strip()

        results.append({
            "prefix": prefix,
            "city_csv": row.get("city", ""),
            "sim_csv": row.get("sim_card", ""),
            "provider_csv": row.get("provider", ""),
            "provider_api": provider,
            "hlr_api": hlr,
            "raw_text": text
        })

        time.sleep(2)

    out_df = pd.DataFrame(results)
    out_df.to_csv(out_file, index=False)
    print(f"💾 Saved: {out_file}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for csv_file in RAW_DIR.glob("*.csv"):
            process_file(csv_file, page)
        browser.close()

if __name__ == "__main__":
    main()
