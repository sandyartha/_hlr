import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

RAW_DIR = Path("raw")
OUT_DIR = Path("raw_checker")
OUT_DIR.mkdir(exist_ok=True)

def process_file(file_path: Path, page):
    print(f"▶️ Processing {file_path.name}")
    df = pd.read_csv(file_path)
    results = []

    for _, row in df.iterrows():
        prefix = str(row["prefix"])
        msisdn = "0" + prefix + "0000000"

        page.goto("https://ceebydith.com/cek-hlr-lokasi-hp.html")

        # pastikan input siap
        try:
            page.wait_for_selector("#msisdn", timeout=10000)
            page.locator("#msisdn").evaluate("el => el.removeAttribute('disabled')")
        except Exception:
            print(f"⚠️ Gagal menemukan input #msisdn untuk {msisdn}")
            continue

        # isi nomor
        page.fill("#msisdn", msisdn)

        # klik tombol
        page.click("#find")

        # tunggu hasil
        try:
            page.wait_for_function(
                """() => {
                    const el = document.querySelector("pre.message");
                    if (!el) return false;
                    const txt = el.innerText;
                    return txt.includes("Operator") || txt.includes("ERROR");
                }""",
                timeout=10000
            )
        except Exception:
            print(f"⚠️ Timeout hasil untuk {msisdn}")
            continue

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

    # simpan hasil
    out_file = OUT_DIR / file_path.name
    if results:
        pd.DataFrame(results).to_csv(out_file, index=False)
        print(f"✅ Saved: {out_file}")
    else:
        print(f"⚠️ No results for {file_path.name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for csv_file in RAW_DIR.glob("*.csv"):
            out_file = OUT_DIR / csv_file.name
            if out_file.exists():
                print(f"⏩ Skip {csv_file.name}, already processed.")
                continue
            process_file(csv_file, page)

        browser.close()


if __name__ == "__main__":
    main()
