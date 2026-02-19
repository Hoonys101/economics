import os
import time
from playwright.sync_api import sync_playwright, expect

def test_macro_canvas(page):
    # Capture console logs
    page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))

    print("Navigating to app...")
    page.goto("http://localhost:5173")

    # Wait for Macro Canvas to load
    print("Waiting for Macro Canvas...")
    expect(page.get_by_text("Macro Canvas")).to_be_visible(timeout=10000)

    # Wait for connection indicator
    print("Waiting for connection...")
    expect(page.get_by_text("Agents Live")).to_be_visible(timeout=30000)

    # Wait for scatter plot to render points
    print("Waiting for scatter points...")
    time.sleep(5) # Give some time for rendering

    # Count svg elements
    svgs = page.locator("svg")
    print(f"Found {svgs.count()} SVGs.")

    # Count paths and circles
    paths = page.locator("path")
    circles = page.locator("circle")
    print(f"Found {paths.count()} paths.")
    print(f"Found {circles.count()} circles.")

    # Try to find symbols
    symbols = page.locator(".recharts-scatter-symbol")
    count = symbols.count()
    print(f"Found {count} .recharts-scatter-symbol elements.")

    if count == 0:
        # Dump HTML of chart area
        chart = page.locator(".recharts-responsive-container")
        if chart.count() > 0:
            print("Chart HTML:", chart.inner_html())
        else:
            print("Chart container not found.")

    # Take debug screenshot
    os.makedirs("verification", exist_ok=True)
    page.screenshot(path="verification/debug_v3.png")

    if count > 0:
        print("Clicking a scatter point...")
        symbols.first.click()

        # Verify Inspector Panel
        print("Verifying Inspector Panel...")
        expect(page.locator("h3").filter(has_text="#")).to_be_visible()
    else:
        print("No points found to click!")
        raise Exception("No scatter points found")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_macro_canvas(page)
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            browser.close()
