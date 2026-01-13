"""Settings routes for the mt music player API."""

from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingValue(BaseModel):
    """Request to update a single setting."""

    value: Any


class SettingsUpdateRequest(BaseModel):
    """Request to update multiple settings."""

    volume: int | None = Field(None, ge=0, le=100)
    shuffle: bool | None = None
    loop_mode: str | None = None
    theme: str | None = None
    sidebar_width: int | None = Field(None, ge=100, le=500)
    queue_panel_height: int | None = Field(None, ge=100, le=800)


@router.get("")
async def get_all_settings(db: DatabaseService = Depends(get_db)):
    """Get all user settings."""
    settings = db.get_all_settings()
    return {"settings": settings}


@router.get("/{key}")
async def get_setting(key: str, db: DatabaseService = Depends(get_db)):
    """Get a specific setting."""
    value = db.get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": value}


@router.put("/{key}")
async def update_setting(key: str, request: SettingValue, db: DatabaseService = Depends(get_db)):
    """Update a setting."""
    db.set_setting(key, request.value)
    return {"key": key, "value": request.value}


@router.put("")
async def bulk_update_settings(request: SettingsUpdateRequest, db: DatabaseService = Depends(get_db)):
    """Bulk update settings."""
    settings_dict = request.model_dump(exclude_none=True)
    updated = db.update_settings(settings_dict)
    return {"updated": updated}
