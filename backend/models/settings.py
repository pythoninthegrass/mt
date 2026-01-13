"""Settings models for user preferences."""

from pydantic import BaseModel, Field
from typing import Any


class Setting(BaseModel):
    """A single setting key-value pair."""

    key: str
    value: Any


class SettingsUpdate(BaseModel):
    """Request to update multiple settings."""

    volume: int | None = Field(None, ge=0, le=100)
    shuffle: bool | None = None
    loop_mode: str | None = Field(None, pattern="^(none|all|one)$")
    library_paths: list[str] | None = None
    theme: str | None = None
    sidebar_width: int | None = Field(None, ge=100, le=500)
    queue_panel_height: int | None = Field(None, ge=100, le=800)


class AllSettings(BaseModel):
    """All user settings."""

    volume: int = 75
    shuffle: bool = False
    loop_mode: str = "none"
    library_paths: list[str] = []
    theme: str = "dark"
    sidebar_width: int = 250
    queue_panel_height: int = 300
