from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.crud.settings import get_all_settings
from app.schemas.configuration import ConfigurationResponse, ConfigurationUpdate
from app.services.configuration_service import ConfigurationConflict, configuration_response, save_configuration

router = APIRouter()


def permission(user: User) -> str | None:
    permissions = getattr(getattr(user, 'role', None), 'permissions', None)
    return permissions.get('settings') if isinstance(permissions, dict) else None


def require_view(user: User) -> None:
    if permission(user) not in ('full', 'view'):
        raise HTTPException(403, 'Not authorized to view system settings')


@router.get('/configuration', response_model=ConfigurationResponse)
def read_configuration_endpoint(response: Response, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_view(user)
    response.headers["Cache-Control"] = "no-store"
    return configuration_response(db, can_edit=permission(user) == 'full')


@router.put('/configuration', response_model=ConfigurationResponse)
def write_configuration_endpoint(update: ConfigurationUpdate, response: Response, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if permission(user) != 'full':
        raise HTTPException(403, 'Not authorized to edit system settings')
    response.headers["Cache-Control"] = "no-store"
    try:
        return save_configuration(db, update, actor_id=user.id)
    except ConfigurationConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, "Settings could not be saved. Your draft is preserved; retry later.") from exc


@router.get('')
def read_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_view(user)
    return {k: v for k, v in get_all_settings(db).items() if k not in
            ('operational_configuration_v1', 'news_automation_runtime_v1')}


@router.put('')
def retired_write(user: User = Depends(get_current_user)):
    if permission(user) != 'full':
        raise HTTPException(403, 'Not authorized to edit system settings')
    raise HTTPException(410, 'Reload System Settings and use the versioned configuration endpoint.')
