from typing import List
from fastapi import APIRouter
from app.services.hotline_service import (
    fetch_and_parse_hotlines,
    fetch_full_hotlines,
    HotlineGroup,
    FullHotlineResponse,
)

router = APIRouter()


@router.get("/", response_model=List[HotlineGroup])
def get_hotlines():
    """
    Returns only national hotlines from ehotlines.e.gov.ph (used by the sidebar widget).
    """
    return fetch_and_parse_hotlines()


@router.get("/full", response_model=FullHotlineResponse)
def get_full_hotlines():
    """
    Returns all hotlines combined:
    - national: all agencies from ehotlines.e.gov.ph
    - pasig_city: Pasig City government agencies
    - pasig_barangay: All Pasig barangay hotlines
    """
    return fetch_full_hotlines()
