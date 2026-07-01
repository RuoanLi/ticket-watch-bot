from __future__ import annotations

import json
from pathlib import Path

import requests


def load_session(cookies_file: str, user_agent: str, referer: str | None = None, origin: str | None = None) -> requests.Session:
    """Build a requests.Session pre-loaded with cookies exported from a logged-in browser.

    cookies_file must be a JSON object of {cookie_name: value}, e.g. produced by
    login_helper.py or a browser cookie-export extension.
    """
    path = Path(cookies_file)
    if not path.exists():
        raise FileNotFoundError(
            f"Cookie file not found: {cookies_file}. "
            "Log into the target site in a browser, export cookies (see login_helper.py), "
            "and save them there before starting the monitor."
        )

    cookies = json.loads(path.read_text())
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/javascript, application/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }
    if referer:
        headers["Referer"] = referer
    if origin:
        headers["Origin"] = origin
    session.headers.update(headers)
    return session
