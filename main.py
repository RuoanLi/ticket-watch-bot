import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Fetch once and print, no Telegram/state writes")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Use a real Playwright browser (fetches from within the page's own JS context) "
        "instead of a raw requests session - needed if the target site's anti-bot layer 403s plain HTTP requests",
    )
    args = parser.parse_args()

    if args.browser:
        from src.browser_monitor import run, run_dry_run
    else:
        from src.monitor import run, run_dry_run

    if args.dry_run:
        run_dry_run()
    else:
        run()
