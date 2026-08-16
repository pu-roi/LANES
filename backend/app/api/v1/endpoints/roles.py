from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.database import get_db
from app.crud.audit import create_audit_log

router = APIRouter()


@router.get("", response_model=List[schemas.RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve roles.
    """
    roles = db.query(models.Role).all()
    return roles


@router.post("", response_model=schemas.RoleResponse)
def create_role(
    *,
    request: Request,
    db: Session = Depends(get_db),
    role_in: schemas.RoleCreate,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Create new role.
    """
    role = db.query(models.Role).filter(models.Role.name == role_in.name).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="The role with this name already exists in the system.",
        )
    role = models.Role(
        name=role_in.name,
        permissions=role_in.permissions,
        is_template=False
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    client_ip = request.client.host if request.client else None
    create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="CREATE_ROLE",
            target_table="roles",
            target_id=role.id,
            metadata_json={
                "role_name": role.name,
                "permissions": role.permissions
            },
            ip_address=client_ip
        )
    )
    
    return role


@router.put("/{role_id}", response_model=schemas.RoleResponse)
def update_role(
    *,
    request: Request,
    db: Session = Depends(get_db),
    role_id: int,
    role_in: schemas.RoleUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Update a role.
    """
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_template:
        raise HTTPException(status_code=400, detail="Cannot modify a template role")
        
    old_name = role.name
    old_permissions = role.permissions
        
    if role_in.name:
        role.name = role_in.name
    if role_in.permissions is not None:
        role.permissions = role_in.permissions
        
    db.add(role)
    db.commit()
    db.refresh(role)
    
    client_ip = request.client.host if request.client else None
    create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="UPDATE_ROLE",
            target_table="roles",
            target_id=role.id,
            metadata_json={
                "old_name": old_name,
                "new_name": role.name,
                "old_permissions": old_permissions,
                "new_permissions": role.permissions
            },
            ip_address=client_ip
        )
    )
    
    return role


@router.delete("/{role_id}")
def delete_role(
    *,
    request: Request,
    db: Session = Depends(get_db),
    role_id: int,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Delete a role.
    """
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_template:
        raise HTTPException(status_code=400, detail="Cannot delete a template role")
        
    # Check if users are assigned to this role
    if len(role.users) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete role with assigned users")
        
    role_name = role.name
    db.delete(role)
    db.commit()
    
    client_ip = request.client.host if request.client else None
    create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="DELETE_ROLE",
            target_table="roles",
            target_id=role_id,
            metadata_json={
                "role_name": role_name
            },
            ip_address=client_ip
        )
    )
    
    return {"message": "Role deleted successfully"}


@router.post("/{role_id}/clone", response_model=schemas.RoleResponse)
def clone_role(
    *,
    request: Request,
    db: Session = Depends(get_db),
    role_id: int,
    new_name: str,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Clone a role.
    """
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    existing = db.query(models.Role).filter(models.Role.name == new_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="A role with this name already exists")
        
    new_role = models.Role(
        name=new_name,
        permissions=role.permissions,
        is_template=False
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    client_ip = request.client.host if request.client else None
    create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="CLONE_ROLE",
            target_table="roles",
            target_id=new_role.id,
            metadata_json={
                "source_role_id": role_id,
                "cloned_role_name": new_role.name
            },
            ip_address=client_ip
        )
    )
    
    return new_role
