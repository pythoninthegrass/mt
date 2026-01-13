"""Favorites models for liked songs and top tracks."""

from datetime import datetime
from pydantic import BaseModel


class FavoriteStatus(BaseModel):
    """Status of whether a track is favorited."""

    is_favorite: bool
    favorited_date: datetime | None = None


class FavoriteAddResponse(BaseModel):
    """Response when adding a track to favorites."""

    success: bool
    favorited_date: datetime
