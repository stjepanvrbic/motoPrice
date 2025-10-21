#!/usr/bin/env python3
"""
Helper script to manually log into Facebook and save session.

This script only needs to be run ONCE to establish a session.
After that, all tests and scrapers will use the saved session.

Usage:
    python scripts/facebookLogin.py

The script will:
1. Open a browser window
2. Log you into Facebook (with CAPTCHA/2FA if needed)
3. Save the session to .facebook_session.json
4. Close the browser

After running this once, integration tests will use the saved session
and run without any manual intervention.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from src.utils.logger import getLogger

# Load environment variables
load_dotenv()

logger = getLogger(__name__)


def manualFacebookLogin():
    """
    Manually log into Facebook and save session.

    This function opens a browser, handles login (including CAPTCHA/2FA),
    and saves the session cookies for future use.
    """
    email = os.getenv("FACEBOOK_EMAIL")
    password = os.getenv("FACEBOOK_PASSWORD")

    if not email or not password:
        logger.error("FACEBOOK_EMAIL and FACEBOOK_PASSWORD must be set in .env file")
        return False

    logger.info("Starting Facebook login process...")
    logger.info(
        "A browser window will open. Please complete login (including CAPTCHA/2FA if needed)"
    )

    playwright = None
    browser = None

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=False,  # Must be visible for CAPTCHA/2FA
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )

        page = context.new_page()

        # Navigate to Facebook login
        logger.info("Navigating to Facebook login page...")
        page.goto("https://www.facebook.com/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Fill in credentials
        logger.info(f"Filling in credentials for {email}...")
        page.fill('input[name="email"]', email)
        time.sleep(1)
        page.fill('input[name="pass"]', password)
        time.sleep(1)

        # Click login
        logger.info("Clicking login button...")
        page.click('button[name="login"]')

        # Give time for page to settle after login
        logger.info("Waiting for login to complete...")
        logger.info("If you see CAPTCHA or 2FA, please complete it in the browser window")
        logger.info("Waiting 30 seconds for you to complete any verification...")
        time.sleep(30)

        # Try to navigate to Facebook home to verify login worked
        try:
            page.goto("https://www.facebook.com/", wait_until="networkidle", timeout=15000)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not navigate to home: {e}")

        # Check if we're successfully logged in by looking for login button
        # If logged in, there should NOT be a login button visible
        try:
            loginButton = page.query_selector('a[href*="/login"]')
            if loginButton and loginButton.is_visible():
                logger.error("Login button still visible - login failed")
                return False
        except Exception:
            pass  # If we can't find login button, assume we're logged in

        logger.info("Successfully logged into Facebook!")

        # Save session cookies
        cookies = context.cookies()
        sessionFile = Path(".facebook_session.json")

        with open(sessionFile, "w") as f:
            json.dump(cookies, f, indent=2)

        logger.info(f"Session saved to {sessionFile}")
        logger.info("=" * 60)
        logger.info("SUCCESS! Session saved.")
        logger.info("You can now run integration tests without manual intervention:")
        logger.info("  pytest -m integration tests/integration/testFacebookIntegration.py")
        logger.info("=" * 60)

        # Close browser
        time.sleep(2)
        browser.close()
        playwright.stop()

        return True

    except Exception as e:
        logger.error(f"Login failed: {e}")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Facebook Manual Login Helper")
    print("=" * 60)
    print()

    success = manualFacebookLogin()

    if success:
        print("\n✓ Login successful! Session saved.")
        print("✓ Integration tests can now run automatically.")
        sys.exit(0)
    else:
        print("\n✗ Login failed. Please try again.")
        sys.exit(1)
