from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(bot_token: str, chat_id: str, text: str, parse_mode: str | None = None) -> bool:
    url = _TELEGRAM_API.format(token=bot_token)
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Failed to send Telegram notification")
        return False


def format_area_alert(
    area_no: str,
    seat_grade_name: str,
    remaining: int,
    timestamp: str,
    seat_map_url: str | None = None,
) -> str:
    lines = [
        "\U0001f6a8 Seat Available!",
        f"Section: {area_no}",
        f"Grade: {seat_grade_name}",
        f"Remaining: {remaining}",
        f"Time: {timestamp}",
    ]
    if seat_map_url:
        lines.append(f'<a href="{seat_map_url}">Open seat map</a>')
    return "\n".join(lines)
