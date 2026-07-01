from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

from src.area_filter import find_available_areas
from src.jsonp_parser import extract_summary, parse_jsonp
from src.state_store import load_seen, save_seen
from src.telegram_notifier import format_area_alert, send_telegram_message

logger = logging.getLogger(__name__)

_FETCH_JS = """
async ({url, data}) => {
    const body = new URLSearchParams(data).toString();
    const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body,
        credentials: 'include'
    });
    return await resp.text();
}
"""


def load_config(config_path: str) -> dict:
    return yaml.safe_load(Path(config_path).read_text())


def fetch_summary_via_page(page, target_cfg: dict) -> list[dict]:
    raw_text = page.evaluate(
        _FETCH_JS,
        {"url": target_cfg["summary_api_url"], "data": target_cfg.get("summary_post_data", {})},
    )
    payload = parse_jsonp(raw_text)
    return extract_summary(payload)


def _open_logged_in_page(target_cfg: dict, headless: bool):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context(user_agent=target_cfg["user_agent"])
    page = context.new_page()
    page.goto(target_cfg.get("start_url", "about:blank"))

    if headless:
        raise RuntimeError("headless mode requires an already-authenticated context; run headful first")

    input(
        "A blank browser window just opened. In THAT window: log in to the target site, navigate to "
        "the event/listing you want, and click through to the availability page until you see real "
        "data (not a blank/placeholder view). Only then come back here and press Enter...\n"
    )

    return playwright, browser, page


def run_dry_run(config_path: str = "config/config.yaml") -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config(config_path)
    target_cfg = config["target"]
    ignore_prefix = config.get("filters", {}).get("ignore_prefix", "4")

    playwright, browser, page = _open_logged_in_page(target_cfg, headless=False)
    try:
        summary = fetch_summary_via_page(page, target_cfg)
        print(f"{len(summary)} area(s) in response:")
        for area in summary:
            print(f"  {area.get('areaNo')}: realSeatCntlk={area.get('realSeatCntlk')}")

        available = find_available_areas(summary, ignore_prefix)
        print(f"\n{len(available)} area(s) currently have seats (excluding {ignore_prefix}xx):")
        for area in available:
            print(f"  -> {area.area_no} ({area.seat_grade_name}): {area.real_seat_cnt} remaining")
    finally:
        browser.close()
        playwright.stop()


def run(config_path: str = "config/config.yaml") -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config(config_path)

    target_cfg = config["target"]
    polling_cfg = config["polling"]
    telegram_cfg = config["telegram"]
    state_cfg = config["state"]
    ignore_prefix = config.get("filters", {}).get("ignore_prefix", "4")

    playwright, browser, page = _open_logged_in_page(target_cfg, headless=False)
    seen = load_seen(state_cfg["seen_file"])
    seat_map_url = target_cfg.get("seat_map_page_url")

    logger.info("Starting seat monitor (browser mode). %d area(s) already seen as available.", len(seen))

    try:
        while True:
            if page.is_closed():
                logger.error("Browser window was closed - stopping. Re-run to start monitoring again "
                              "and keep the window open this time.")
                break

            try:
                summary = fetch_summary_via_page(page, target_cfg)
                available = find_available_areas(summary, ignore_prefix)

                current_areas = {area.area_no for area in available}
                newly_available = [a for a in available if a.area_no not in seen]

                for area in newly_available:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    text = format_area_alert(
                        area.area_no, area.seat_grade_name, area.real_seat_cnt, timestamp, seat_map_url
                    )
                    logger.info("Section now available: %s", text.replace("\n", " | "))
                    send_telegram_message(
                        telegram_cfg["bot_token"], telegram_cfg["chat_id"], text, parse_mode="HTML"
                    )

                if current_areas != seen:
                    seen = current_areas
                    save_seen(state_cfg["seen_file"], seen)

            except Exception:
                logger.exception("Poll cycle failed, will retry after backoff")

            sleep_for = random.uniform(polling_cfg["min_interval_sec"], polling_cfg["max_interval_sec"])
            time.sleep(sleep_for)
    finally:
        if not browser.is_connected():
            playwright.stop()
            return
        browser.close()
        playwright.stop()
