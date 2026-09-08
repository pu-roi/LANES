from typing import List
from fastapi import APIRouter
from app.services.hotline_service import (
    fetch_and_parse_hotlines,
    fetch_full_hotlines,
    HotlineGroup,
    FullHotlineResponse,
)

router = APIRouter()


@router.get("", response_model=List[HotlineGroup])
@router.get("/", response_model=List[HotlineGroup], include_in_schema=False)
def get_hotlines():
    """
    Returns only national hotlines from ehotlines.e.gov.ph (used by the sidebar widget).
    """
    return fetch_and_parse_hotlines()


@router.get("/full", response_model=FullHotlineResponse)
@router.get("/full/", response_model=FullHotlineResponse, include_in_schema=False)
def get_full_hotlines():
    """
    Returns all hotlines combined:
    - national: all agencies from ehotlines.e.gov.ph
    - pasig_city: Pasig City government agencies
    - pasig_barangay: All Pasig barangay hotlines
    """
    return fetch_full_hotlines()
