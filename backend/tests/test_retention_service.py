import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from app.services.retention_service import purge_expired_archived_records
from app import models


def test_purge_expired_records_mocked_db():
    mock_db = MagicMock()
    
    # Setup mock returns
    now = datetime.utcnow()
    expired_user = models.User(
        id=99,
        username="expired_user",
        email="expired@test.com",
        deleted_at=now - timedelta(days=35)
    )
    
    # Configure mock query
    mock_db.query.return_value.filter.return_value.all.side_effect = [
        [expired_user],  # Users
        [],               # Posts
        [],               # Reports
        []                # Zones
    ]

    results = purge_expired_archived_records(db=mock_db, retention_days=30)
    
    assert results["users"] == 1
    assert results["total"] == 1
    assert mock_db.delete.called
    assert mock_db.commit.called
