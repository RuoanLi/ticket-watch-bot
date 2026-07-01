# Seat/Inventory Availability Monitor

A personal-use tool that polls a ticketing (or similar inventory) site's
availability API and sends a Telegram alert the moment a specific
section/SKU goes from sold-out to available. Notify-only — it never adds
to cart or purchases anything; you still act on the alert yourself.

Built for a real event where the venue's public "seat map" endpoint only
exposed *price tier*, not actual per-section availability - the real
signal turned out to live in a separate per-section summary endpoint that
returns every section's remaining count in a single request. That's the
pattern this project is built around: find the lightweight endpoint that
gives you granular state in one call, poll it politely, and alert on
state transitions rather than every poll.

## How it works

1. `jsonp_parser` strips the JSONP callback wrapper (and any `/**/`
   comment prefix some APIs add) and returns plain JSON.
2. `area_filter` picks out sections with remaining count > 0, excluding
   any section matching an ignore-prefix (configurable).
3. `state_store` tracks which sections were already known-available, so
   alerts only fire on a 0 → >0 transition, not every poll.
4. `telegram_notifier` sends the alert.
5. `monitor` / `browser_monitor` are the two poll-loop implementations
   (see below).

## Two run modes

Some sites sit behind a bot-detection layer that rejects plain HTTP
requests even with valid session cookies and matching headers.

- **`python main.py`** - plain `requests` session (`src/monitor.py`).
  Simple and lightweight.
- **`python main.py --browser`** - drives a real Playwright/Chromium
  browser and calls `fetch()` from inside the page's own JS context
  (`src/browser_monitor.py`), so requests come from an actual browser
  session rather than a script pretending to be one. Keeps a visible
  browser window open for the whole monitoring session; you log in once
  when it starts, then the poll loop reuses that live session.

## Setup

1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `cp config/config.yaml.example config/config.yaml` and fill in your
   target site's real endpoint URL, POST params, and headers (grab these
   from your browser's Network tab while browsing the site normally).
4. Cookies (only needed for the non-`--browser` mode):
   - `python login_helper.py`, log in manually in the browser window that
     opens, press Enter in the terminal - cookies get saved to
     `config/cookies.json`.
   - Or export cookies manually from your browser's devtools into that
     same file (see `config/cookies.json.example` for the format).
5. Telegram: create a bot via [@BotFather](https://t.me/BotFather), message
   it once, then hit `https://api.telegram.org/bot<token>/getUpdates` to
   find your chat_id. Fill both into `config/config.yaml`.
6. `python main.py --browser --dry-run` to fetch once and print current
   per-section counts without sending Telegram messages or writing state.
7. `python main.py --browser` to start monitoring for real.

## Notes

- Polls every 3-5s with a randomized interval and only alerts on state
  transitions, not on every poll while a section stays available.
- Automated polling likely falls under most ticketing sites' bot /
  automated-access restrictions - this is meant for personal, low-volume
  use, not for reselling or high-volume automated purchasing. It also
  deliberately stops short of any add-to-cart/checkout automation.
- `config/config.yaml` and `config/cookies.json` hold live session
  credentials once filled in - both are gitignored. Don't commit or share
  them.
