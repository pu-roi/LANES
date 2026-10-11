import pytest

from scripts.seed_local_news_replay import require_local_test_database


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_accepts_only_dedicated_loopback_database(host: str) -> None:
    require_local_test_database(f"postgresql+psycopg://{host}/lanes_news_test")


@pytest.mark.parametrize("url", [
    "postgresql+psycopg://cloud.example/lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes",
    "sqlite:///lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?host=cloud.example",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?hostaddr=203.0.113.1",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?service=production",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?dbname=lanes",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?database=lanes",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?port=6543",
])
def test_refuses_cloud_existing_local_and_connection_override_targets(url: str) -> None:
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        require_local_test_database(url)
