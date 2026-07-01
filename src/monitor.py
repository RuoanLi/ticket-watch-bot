from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from pathlib import Path

import yaml

from src.area_filter import find_available_areas
from src.jsonp_parser import extract_summary, parse_jsonp
from src.session_manager import load_session
from src.state_store import load_seen, save_seen
from src.telegram_notifier import format_area_alert, send_telegram_message

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    return yaml.safe_load(Path(config_path).read_text())


def fetch_summary(session, target_cfg: dict) -> list[dict]:
    resp = session.post(
        target_cfg["summary_api_url"],
        data=target_cfg.get("summary_post_data", {}),
        timeout=target_cfg.get("request_timeout", 10),
    )
    resp.raise_for_status()
    payload = parse_jsonp(resp.text)
    return extract_summary(payload)


def run_dry_run(config_path: str = "config/config.yaml") -> None:
    """Fetch the area summary once and print current remaining counts, without touching Telegram or state."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config(config_path)
    target_cfg = config["target"]
    ignore_prefix = config.get("filters", {}).get("ignore_prefix", "4")

    session = load_session(
        target_cfg["cookies_file"], target_cfg["user_agent"], target_cfg.get("referer"), target_cfg.get("origin")
    )
    summary = fetch_summary(session, target_cfg)

    print(f"{len(summary)} area(s) in response:")
    for area in summary:
        print(f"  {area.get('areaNo')}: realSeatCntlk={area.get('realSeatCntlk')}")

    available = find_available_areas(summary, ignore_prefix)
    print(f"\n{len(available)} area(s) currently have seats (excluding {ignore_prefix}xx):")
    for area in available:
        print(f"  -> {area.area_no} ({area.seat_grade_name}): {area.real_seat_cnt} remaining")


def run(config_path: str = "config/config.yaml") -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config(config_path)

    target_cfg = config["target"]
    polling_cfg = config["polling"]
    telegram_cfg = config["telegram"]
    state_cfg = config["state"]
    ignore_prefix = config.get("filters", {}).get("ignore_prefix", "4")

    session = load_session(
        target_cfg["cookies_file"], target_cfg["user_agent"], target_cfg.get("referer"), target_cfg.get("origin")
    )
    seen = load_seen(state_cfg["seen_file"])
    seat_map_url = target_cfg.get("seat_map_page_url")

    logger.info("Starting seat monitor. %d area(s) already seen as available.", len(seen))

    while True:
        try:
            summary = fetch_summary(session, target_cfg)
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
