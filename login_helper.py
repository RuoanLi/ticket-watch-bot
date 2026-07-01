"""
One-time helper to export session cookies for the monitor to reuse.

Opens a real browser window pointed at the target site's login page. You log in
yourself (including any 2FA/captcha), then press Enter in the terminal once
you're in. The script then saves your session cookies to config/cookies.json.

This does NOT automate the login itself - it only captures the cookies from
a session you authenticated by hand. Reads login_url / cookie_domain from
config/config.yaml (target.login_url, target.cookie_domain).
"""

import json
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

CONFIG_PATH = Path("config/config.yaml")
COOKIES_OUT = Path("config/cookies.json")


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text())
    target_cfg = config["target"]
    login_url = target_cfg["login_url"]
    cookie_domain = target_cfg["cookie_domain"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(login_url)

        input("Log in in the opened browser window, then press Enter here...")

        cookies = page.context.cookies()
        relevant_cookies = {c["name"]: c["value"] for c in cookies if cookie_domain in c["domain"]}

        COOKIES_OUT.parent.mkdir(parents=True, exist_ok=True)
        COOKIES_OUT.write_text(json.dumps(relevant_cookies, indent=2))
        print(f"Saved {len(relevant_cookies)} cookies to {COOKIES_OUT}")

        browser.close()


if __name__ == "__main__":
    main()
