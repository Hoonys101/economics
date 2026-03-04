from playwright.sync_api import sync_playwright, expect
import time
import requests
import json
import multiprocessing
import sys

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    return False

def run_app():
    import sys
    sys.path.append("dashboard")
    from app import app
    app.config["TESTING"] = True
    app.run(port=5005, debug=False, use_reloader=False)

def test_frontend_flow():
    server_process = multiprocessing.Process(target=run_app, daemon=True)
    server_process.start()

    base_url = "http://127.0.0.1:5005"
    if not wait_for_server(base_url):
        print("Server failed to start")
        server_process.terminate()
        return

    try:
        import config
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(base_url)
            expect(page).to_have_title("경제 시뮬레이션 대시보드 (v2)")

            page.evaluate(f"localStorage.setItem('secretToken', '{config.SECRET_TOKEN}')")
            page.reload()

            start_button = page.get_by_role("button", name="Start Simulation")
            if start_button.is_visible():
                start_button.click()
                expect(page.get_by_role("button", name="Pause Simulation")).to_be_visible()

            page.wait_for_selector("canvas", timeout=10000)
            expect(page.locator("canvas").first).to_be_visible()

            page.get_by_role("button", name="Stop Simulation").click()

            screenshot_path = "design/test_reports/e2e_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

            browser.close()
            print("E2E Test Completed Successfully")
    finally:
        print("Terminating server process...")
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    test_frontend_flow()
