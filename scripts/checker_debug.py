import asyncio
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://ceebydith.com/cek-hlr-lokasi-hp.html"

def log_debug(message: str):
    """Helper function untuk print debug message dengan timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[DEBUG {timestamp}] {message}")

async def check_number(page, msisdn: str) -> dict:
    """Cek 1 nomor di halaman HLR lookup dengan debug messages yang detail"""
    log_debug(f"🌐 Membuka URL: {URL}")
    await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    log_debug("✅ Halaman berhasil dibuka")

    # tunggu input aktif
    log_debug("⏳ Menunggu input field menjadi aktif...")
    await page.wait_for_selector("#msisdn:not([disabled])", timeout=10000)
    log_debug("✅ Input field sudah aktif")

    # isi nomor
    log_debug(f"📝 Mengisi nomor: {msisdn}")
    await page.fill("#msisdn", msisdn)
    log_debug("✅ Nomor berhasil diisi")

    # tunggu tombol aktif lalu klik
    log_debug("⏳ Menunggu tombol cek menjadi aktif...")
    await page.wait_for_selector("#find:not([disabled])", timeout=5000)
    log_debug("🖱️ Mengklik tombol cek")
    await page.click("#find")

    # tunggu hasil
    log_debug("⏳ Menunggu hasil pengecekan...")
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
        log_debug("✅ Hasil ditemukan")
        log_debug(f"📄 Raw response:\n{text}")
    except Exception as e:
        log_debug(f"⚠️ Timeout untuk {msisdn}: {str(e)}")
        return {"provider": None, "hlr": None, "raw_text": "", "error": str(e)}

    # parsing hasil
    provider, hlr = None, None
    for line in text.splitlines():
        if "Operator" in line:
            provider = line.split(":", 1)[1].strip()
            log_debug(f"📱 Provider terdeteksi: {provider}")
        elif "HLR" in line:
            hlr = line.split(":", 1)[1].strip()
            log_debug(f"📍 HLR terdeteksi: {hlr}")

    return {
        "provider": provider,
        "hlr": hlr,
        "raw_text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

async def check_single_number(playwright, msisdn: str):
    """Debug checker untuk satu nomor"""
    log_debug(f"🚀 Memulai pengecekan untuk nomor: {msisdn}")
    
    try:
        log_debug("🌐 Menginisialisasi browser...")
        browser = await playwright.chromium.launch(headless=True)
        log_debug("✅ Browser berhasil diinisialisasi")
        
        log_debug("📝 Membuat halaman baru...")
        page = await browser.new_page()
        log_debug("✅ Halaman baru siap")

        try:
            log_debug("🔍 Memulai proses pengecekan...")
            result = await check_number(page, msisdn)
            
            log_debug("\n=== HASIL PENGECEKAN ===")
            log_debug(f"📱 Provider: {result['provider']}")
            log_debug(f"📍 HLR: {result['hlr']}")
            log_debug(f"⏰ Waktu: {result['timestamp']}")
            log_debug("=====================")

        except Exception as e:
            log_debug(f"❌ Error dalam pengecekan: {str(e)}")
            result = {"provider": None, "hlr": None, "raw_text": "", "error": str(e)}

    except Exception as e:
        log_debug(f"❌ Error dalam inisialisasi browser: {str(e)}")
        result = {"provider": None, "hlr": None, "raw_text": "", "error": str(e)}
    
    finally:
        if 'browser' in locals():
            log_debug("🔒 Menutup browser...")
            await browser.close()
            log_debug("✅ Browser ditutup")

    return result

async def main():
    log_debug("🏁 Program debug checker dimulai")
    
    try:
        msisdn = input("Masukkan nomor yang ingin dicek (contoh: 08123456789): ")
        if not msisdn.startswith("0") or not msisdn.isdigit():
            log_debug("❌ Format nomor tidak valid. Harus dimulai dengan '0' dan hanya berisi angka")
            return
        
        log_debug(f"🎯 Nomor yang akan dicek: {msisdn}")
        
        async with async_playwright() as p:
            await check_single_number(p, msisdn)
            
    except KeyboardInterrupt:
        log_debug("\n👋 Program dihentikan oleh user")
    except Exception as e:
        log_debug(f"❌ Error tidak terduga: {str(e)}")
    
    log_debug("🏁 Program selesai")

if __name__ == "__main__":
    asyncio.run(main())