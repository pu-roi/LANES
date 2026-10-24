"""Mandatory CI tests with an explicitly disposable sibling PostGIS container."""
import os
from pathlib import Path


def main() -> None:
    database = os.environ.get('POSTGRES_DB', '')
    password = os.environ.get('POSTGRES_PASSWORD', '')
    if not database.startswith('lanes_settings_test_') or not password:
        raise SystemExit('Mandatory disposable history database configuration missing')
    from sqlalchemy.engine import URL
    value = URL.create('postgresql+psycopg', username='postgres', password=password,
                       host='127.0.0.1', port=5432, database=database).render_as_string(hide_password=False)
    os.environ['LANES_SETTINGS_TEST_DATABASE_URL'] = value
    os.environ['DATABASE_URL'] = value
    os.environ['LANES_REQUIRE_HISTORY_MEDIA_TESTS'] = '1'
    import pytest
    result = pytest.main(['tests/test_history_media_postgres.py', 'tests/test_flood_history_authorization.py',
                          'tests/test_news_tribune_pilot.py',
                          '--confcutdir=tests', '-q', '--tb=short', '-p', 'no:cacheprovider'])
    if result:
        raise SystemExit(result)
    # The fixture tests a fresh migration; verify repeated upgrades as well.
    from alembic import command
    from alembic.config import Config
    from app.core.config import settings
    settings.DATABASE_URL = value
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'alembic'))
    command.upgrade(config, 'head')
    print('Mandatory history PostGIS checks and repeated migration passed')


if __name__ == '__main__':
    main()
