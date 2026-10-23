"""Nonsecret production reader selection, packaged independently of inference assets."""
from pathlib import Path


READER_MANIFEST_SHA256 = "005cfaceff31f8faeab174dd7449a6a0fa721797b3a95407ec726574c485f480"
READER_CONTAINER_PATH = "/data/news-reader/read-context.json"
READER_SOURCE_PATH = Path(__file__).resolve().parents[2] / "runtime_data/news-reader/read-context.json"


def production_reader_environment() -> dict[str, str]:
    return {
        "LANES_NEWS_NATIVE_READ_REQUIRED": "1",
        "LANES_NEWS_NATIVE_READ_CONTEXT": READER_CONTAINER_PATH,
        "LANES_NEWS_NATIVE_READ_CONTEXT_SHA256": READER_MANIFEST_SHA256,
    }
