"""Synchronize Pasig ML deadlines and expire due zones using the real/scoped clock.

This operator command writes the configured database. It does not discover news
or invoke external AI providers. No artificial future-clock override is exposed.
"""
import argparse
import time

from app.core.database import SessionLocal
from app.services.flood_event_service import expire_due_zones


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, help="Repeat every 30–3600 seconds; otherwise run once.")
    args = parser.parse_args()
    if args.interval is not None and not 30 <= args.interval <= 3600:
        parser.error("Interval must be 30–3600 seconds.")
    while True:
        with SessionLocal() as db:
            expired = expire_due_zones(db)
        print(f"Zone expiry synchronized; expired={expired}", flush=True)
        if args.interval is None:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
