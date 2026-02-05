from playwright.sync_api import sync_playwright, expect
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Overview
    print("Navigating to Overview...")
    page.goto("http://localhost:3000")
    # Verify connecting state
    expect(page.get_by_text("Connecting to The Watchtower")).to_be_visible()

    # Sidebar Check
    print("Checking Sidebar...")
    expect(page.get_by_text("The Watchtower", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Overview")).to_be_visible()
    expect(page.get_by_role("link", name="Finance")).to_be_visible()

    # Screenshot Overview
    if not os.path.exists("verification"):
        os.makedirs("verification")
    page.screenshot(path="verification/overview.png")

    # Finance
    print("Navigating to Finance...")
    page.click("text=Finance")
    expect(page).to_have_url("http://localhost:3000/finance")
    expect(page.get_by_text("Awaiting financial data")).to_be_visible()
    page.screenshot(path="verification/finance.png")

    # Politics
    print("Navigating to Politics...")
    page.click("text=Politics")
    expect(page).to_have_url("http://localhost:3000/politics")
    expect(page.get_by_text("Awaiting political data")).to_be_visible()
    page.screenshot(path="verification/politics.png")

    # System
    print("Navigating to System...")
    page.click("text=System")
    expect(page).to_have_url("http://localhost:3000/system")
    # System page shows the header even if disconnected, and status
    expect(page.get_by_text("System Diagnostics")).to_be_visible()
    expect(page.get_by_text("Disconnected")).to_be_visible()
    page.screenshot(path="verification/system.png")

    browser.close()
    print("Verification complete.")

with sync_playwright() as playwright:
    run(playwright)
