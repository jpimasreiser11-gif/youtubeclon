from playwright.sync_api import sync_playwright
import os
import time

def capture_auth():
    print("=== TikTok Auth Capture Tool ===")
    print("This script will open a browser window.")
    print("1. Log in to TikTok manually.")
    print("2. Solve any CAPTCHAs.")
    print("3. Once logged in, close the browser window to save the session.")
    
    auth_dir = "auth"
    os.makedirs(auth_dir, exist_ok=True)
    auth_path = os.path.join(auth_dir, "tiktok_state.json")

    with sync_playwright() as p:
        # Launch non-headless browser
        print("Launching Edge browser for better compatibility...")
        try:
            browser = p.chromium.launch(headless=False, channel="msedge")
        except:
            print("Edge not found, trying Chrome...")
            browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context()
        page = context.new_page()

        print("\nOpening TikTok Login...")
        try:
            page.goto("https://www.tiktok.com/login")
        except Exception as e:
            print(f"Error loading page: {e}")

        # Wait for user to close the browser (or handle a signal)
        # We can poll for context state or just wait for input
        print("\n--> Press ENTER in this terminal once you have successfully logged in and the page is loaded.")
        input()
        
        print("Saving session state...")
        context.storage_state(path=auth_path)
        print(f"Session saved to {auth_path}")
        
        browser.close()

if __name__ == "__main__":
    capture_auth()
