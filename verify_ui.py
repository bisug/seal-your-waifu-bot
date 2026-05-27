from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    try:
        page.goto("http://localhost:8000")
        page.wait_for_timeout(2000)
        page.screenshot(path="verification.png")
    except Exception as e:
        print(f"Error during CUJ: {e}")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
