"""Read-only provider verification; no application DB, worker, or cloud writes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import httpx
from app.services.news_weather_service import CATALOG_VERSION, POINTS, choose_interval, fetch_weather


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional public scheduling-signal JSON capture")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    with httpx.Client(timeout=httpx.Timeout(10, connect=5), follow_redirects=False) as client:
        providers = fetch_weather(client, now=now)
    payload = {"read_only": True, "checked_at": now.isoformat(), "catalog_version": CATALOG_VERSION,
        "points": [p.model_dump(mode="json") for p in POINTS],
        "providers": [p.model_dump(mode="json") for p in providers],
        "decision": choose_interval(providers, now=now).model_dump(mode="json")}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered+"\n", encoding="utf-8")
        print("Public weather probe saved")
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return int(any(p.status == "unavailable" for p in providers))


if __name__ == "__main__":
    raise SystemExit(main())
