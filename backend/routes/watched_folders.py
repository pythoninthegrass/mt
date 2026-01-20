from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter(prefix="/watched-folders", tags=["watched-folders"])


class WatchedFolderCreate(BaseModel):
    path: str
    mode: Literal["startup", "continuous"] = "startup"
    cadence_minutes: int = Field(default=10, ge=1, le=1440)
    enabled: bool = True


class WatchedFolderUpdate(BaseModel):
    mode: Literal["startup", "continuous"] | None = None
    cadence_minutes: int | None = Field(default=None, ge=1, le=1440)
    enabled: bool | None = None


@router.get("")
async def list_watched_folders(db: DatabaseService = Depends(get_db)):
    folders = db.get_watched_folders()
    return {"folders": folders}


@router.get("/{folder_id}")
async def get_watched_folder(folder_id: int, db: DatabaseService = Depends(get_db)):
    folder = db.get_watched_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail=f"Watched folder with id {folder_id} not found")
    return folder


@router.post("", status_code=201)
async def add_watched_folder(request: WatchedFolderCreate, db: DatabaseService = Depends(get_db)):
    import os

    if not os.path.isdir(request.path):
        raise HTTPException(status_code=400, detail=f"Path does not exist or is not a directory: {request.path}")

    folder = db.add_watched_folder(
        path=request.path,
        mode=request.mode,
        cadence_minutes=request.cadence_minutes,
        enabled=request.enabled,
    )
    if not folder:
        raise HTTPException(status_code=500, detail="Failed to create watched folder")
    return folder


@router.patch("/{folder_id}")
async def update_watched_folder(
    folder_id: int,
    request: WatchedFolderUpdate,
    db: DatabaseService = Depends(get_db),
):
    existing = db.get_watched_folder(folder_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Watched folder with id {folder_id} not found")

    folder = db.update_watched_folder(
        folder_id=folder_id,
        mode=request.mode,
        cadence_minutes=request.cadence_minutes,
        enabled=request.enabled,
    )
    return folder


@router.delete("/{folder_id}", status_code=204)
async def remove_watched_folder(folder_id: int, db: DatabaseService = Depends(get_db)):
    if not db.remove_watched_folder(folder_id):
        raise HTTPException(status_code=404, detail=f"Watched folder with id {folder_id} not found")


@router.post("/{folder_id}/rescan")
async def rescan_watched_folder(folder_id: int, db: DatabaseService = Depends(get_db)):
    folder = db.get_watched_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail=f"Watched folder with id {folder_id} not found")

    from backend.services.scanner_2phase import parse_changed_files, scan_library_2phase

    db_fingerprints = db.get_all_fingerprints()
    changes, stats = scan_library_2phase([folder["path"]], db_fingerprints, recursive=True)

    files_to_parse = changes["added"] + changes["modified"]
    parsed_files = []
    if files_to_parse:
        parsed_files = parse_changed_files(files_to_parse, parallel=True)

    added_set = {fp for fp, _ in changes["added"]}
    files_to_add = [(fp, meta) for fp, meta in parsed_files if fp in added_set]
    files_to_update = [(fp, meta) for fp, meta in parsed_files if fp not in added_set]

    added = 0
    updated = 0
    deleted = 0

    if files_to_add:
        added = db.add_tracks_bulk(files_to_add)
    if files_to_update:
        updated = db.update_tracks_bulk(files_to_update)
    if changes["deleted"]:
        deleted = db.delete_tracks_bulk(changes["deleted"])

    db.update_watched_folder_last_scanned(folder_id)

    return {
        "folder_id": folder_id,
        "added": added,
        "updated": updated,
        "deleted": deleted,
        "scanned": stats.visited,
    }
