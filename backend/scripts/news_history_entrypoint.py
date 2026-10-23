"""Run the historical parent beneath the already qualified Linux supervisor."""
import sys

from scripts.news_ner_cloud_entrypoint import supervise


def main() -> int:
    return supervise([sys.executable, '-B', '-m', 'scripts.run_news_history_seed', *sys.argv[1:]])


if __name__ == '__main__':
    raise SystemExit(main())
