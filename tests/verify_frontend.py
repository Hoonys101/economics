import time
from playwright.sync_api import sync_playwright

def verify_frontend():
    print("Starting frontend verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='ko-KR'
        )
        page = context.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser Error: {err}"))

        try:
            # Visit the frontend
            url = "http://localhost:5173"
            print(f"Visiting {url}...")

            try:
                page.goto(url, timeout=10000)
            except Exception as e:
                print(f"Goto failed: {e}")
                # Retry once
                time.sleep(2)
                page.goto(url, timeout=10000)

            # Check if we are stuck on loading
            print("Checking page content...")

            # Wait a bit for JS to execute
            page.wait_for_timeout(2000)

            # Check for loading text
            if page.get_by_text("데이터 로딩 중...").is_visible():
                print("State: Loading Data...")
                # Wait longer for it to disappear
                try:
                    # Wait for "사회" (Society) tab which appears when loaded
                    page.wait_for_selector("text=사회", timeout=30000)
                except Exception as e:
                    print("Timed out waiting for dashboard content.")
                    # Take screenshot of loading state
                    page.screenshot(path="frontend_verify_stuck_loading.png")
                    raise e

            # Wait for the "Society" tab text to ensure main content is loaded
            print("Waiting for dashboard content (Society tab)...")
            page.wait_for_selector("text=사회", timeout=10000)

            # Take initial screenshot (Society Tab is default)
            print("Capturing Society tab...")
            page.screenshot(path="frontend_verify_tab_society.png")

            # Click Government
            print("Clicking Government tab...")
            page.click("button:has-text('정부')")
            page.wait_for_timeout(1000) # Wait for transition
            page.screenshot(path="frontend_verify_tab_government.png")

            # Click Market
            print("Clicking Market tab...")
            page.click("button:has-text('시장')")
            page.wait_for_timeout(1000)
            page.screenshot(path="frontend_verify_tab_market.png")

            # Click Finance
            print("Clicking Finance tab...")
            page.click("button:has-text('금융')")
            page.wait_for_timeout(1000)
            page.screenshot(path="frontend_verify_tab_finance.png")

            print("Verification complete. Screenshots saved.")

        except Exception as e:
            print(f"Verification failed: {e}")
            try:
                page.screenshot(path="frontend_verify_error.png")
            except:
                pass
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
