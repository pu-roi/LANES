"""Report evidence must not disappear when a media upload fails."""

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1.endpoints import reports


def test_failed_media_upload_prevents_report_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports, "upload_image", lambda _file: None)

    async def unexpected_report_creation(**_kwargs: object) -> None:
        raise AssertionError("A report with missing selected media must not be created")

    monkeypatch.setattr(reports, "process_new_report", unexpected_report_creation)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(reports.create_report(
            raw_text="Flooded street",
            source="direct_user",
            media=[UploadFile(filename="phone-photo.heic", file=BytesIO(b"photo"))],
            geometry=None,
            survey_data=None,
            db=None,
            current_user=SimpleNamespace(id=1),
        ))

    assert raised.value.status_code == 502
    assert "phone-photo.heic" in raised.value.detail
