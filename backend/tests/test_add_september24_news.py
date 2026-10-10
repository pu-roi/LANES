"""The explicit article addition must reject unintended targets before writes."""
import pytest

from scripts.add_september24_news import add_article


@pytest.mark.asyncio
async def test_addition_refuses_another_database():
    with pytest.raises(ValueError, match="explicitly selected database"):
        await add_article(expected_database="not_the_configured_database", write=True)


@pytest.mark.asyncio
async def test_addition_requires_explicit_write():
    from app.core.database import engine
    with pytest.raises(ValueError, match="Explicit --write"):
        await add_article(expected_database=engine.url.database, write=False)
