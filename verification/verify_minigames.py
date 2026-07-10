from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    # Use backend port where static files are served
    page.goto("http://localhost:8000")
    page.wait_for_timeout(3000)

    # Inject token into sessionStorage
    page.evaluate("sessionStorage.setItem('auth_token', 'a762efd9-e79a-4574-a83d-eaab0e86bcc0')")

    # Reload and wait
    page.goto("http://localhost:8000/#minigames")
    page.wait_for_timeout(10000)

    print(f"Title: {page.title()}")
    page.screenshot(path="verification/screenshots/initial.png")

    # Start Cipher Match
    try:
        game_card = page.get_by_text("Cipher Match")
        game_card.wait_for(state="visible", timeout=15000)
        game_card.click()
    except Exception as e:
        print(f"Cipher Match click failed: {e}")
        page.screenshot(path="verification/screenshots/error_cipher.png")
        print(f"Page content: {page.locator('body').inner_text()[:500]}")
        return

    page.wait_for_timeout(2000)
    page.screenshot(path="verification/screenshots/cipher_match_start.png")

    # Flip a card
    cards = page.locator(".perspective-1000")
    if cards.count() > 0:
        cards.nth(0).click()
        page.wait_for_timeout(1000)
        page.screenshot(path="verification/screenshots/cipher_match_flip.png")

    # Cancel game
    page.get_by_role("button", name="Abort").click()
    page.wait_for_timeout(1000)

    # Start Nexus Wheel
    page.get_by_text("Nexus Wheel").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="verification/screenshots/nexus_wheel_start.png")

    # Spin the wheel
    page.get_by_role("button", name="Initiate Sequence").click()
    page.wait_for_timeout(3000)
    page.screenshot(path="verification/screenshots/nexus_wheel_spinning.png")

    page.wait_for_timeout(6000)
    page.screenshot(path="verification/screenshots/nexus_wheel_result.png")

    # Final state
    page.screenshot(path="verification/screenshots/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification/videos",
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
