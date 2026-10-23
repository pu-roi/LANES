"""Preserve qualified PID-1 supervision for the manual verification worker."""
import sys
from scripts.news_ner_cloud_entrypoint import supervise


def main() -> int:
    return supervise([sys.executable,'-B','-m','scripts.run_news_verified_cloud',*sys.argv[1:]])


if __name__=='__main__':raise SystemExit(main())
