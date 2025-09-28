#!/usr/bin/env python3
"""FastAPI endpoints for music library scanning with WebSocket support."""

import asyncio
from core.scan_async import ScanProgress, ZigScannerAsync
from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pathlib import Path
from pydantic import BaseModel


class ScanRequest(BaseModel):
    """Request model for scanning operations."""
    
    root_path: str
    max_depth: int = 10
    follow_symlinks: bool = False
    skip_hidden: bool = True
    batch_size: int = 100


class ScanResponse(BaseModel):
    """Response model for scanning operations."""
    
    total_files: int
    total_dirs: int
    total_size: int
    scan_duration_ms: float
    files_per_second: float


class BenchmarkRequest(BaseModel):
    """Request model for benchmarking."""
    
    root_path: str
    iterations: int = 3
    warmup: bool = True


router = APIRouter(prefix="/api/scan", tags=["scanning"])

# Global scanner instance
scanner = ZigScannerAsync(max_workers=4)

# Active WebSocket connections
active_connections: set[WebSocket] = set()


@router.post("/start", response_model=ScanResponse)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
) -> ScanResponse:
    """Start a directory scan.
    
    Args:
        request: Scan configuration
        background_tasks: FastAPI background task manager
        
    Returns:
        Scan statistics
    """
    # Validate path
    path = Path(request.root_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.root_path}")
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {request.root_path}")
    
    # Run scan
    stats = await scanner.scan_directory_async(
        root_path=request.root_path,
        max_depth=request.max_depth,
        follow_symlinks=request.follow_symlinks,
        skip_hidden=request.skip_hidden,
        batch_size=request.batch_size,
    )
    
    return ScanResponse(
        total_files=stats.total_files,
        total_dirs=stats.total_dirs,
        total_size=stats.total_size,
        scan_duration_ms=stats.scan_duration_ms,
        files_per_second=stats.files_per_second,
    )


@router.websocket("/ws")
async def websocket_scan(websocket: WebSocket):
    """WebSocket endpoint for real-time scan progress updates.
    
    Client sends:
    {
        "action": "start_scan",
        "data": {
            "root_path": "/path/to/music",
            "max_depth": 10,
            "follow_symlinks": false,
            "skip_hidden": true,
            "batch_size": 100
        }
    }
    
    Server sends:
    {
        "type": "scan_progress",
        "data": {
            "total_files": 1000,
            "processed_files": 500,
            "current_path": "/path/to/current/file.mp3",
            "percentage": 50.0,
            "files_per_second": 250.5,
            "estimated_time_remaining": 2.0
        }
    }
    
    Or on completion:
    {
        "type": "scan_complete",
        "data": {
            "total_files": 1000,
            "total_dirs": 50,
            "total_size": 5000000000,
            "scan_duration_ms": 4000.0,
            "files_per_second": 250.0
        }
    }
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("action") == "start_scan":
                scan_data = data.get("data", {})
                
                # Validate path
                path = Path(scan_data.get("root_path", ""))
                if not path.exists():
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Path not found: {path}"
                    })
                    continue
                
                # Progress callback
                async def send_progress(progress: ScanProgress):
                    await websocket.send_json({
                        "type": "scan_progress",
                        "data": {
                            "total_files": progress.total_files,
                            "processed_files": progress.processed_files,
                            "current_path": progress.current_path,
                            "percentage": progress.percentage,
                            "files_per_second": progress.files_per_second,
                            "estimated_time_remaining": progress.estimated_time_remaining,
                        }
                    })
                
                # Run scan with WebSocket updates
                stats = await scanner.scan_directory_async(
                    root_path=scan_data.get("root_path"),
                    max_depth=scan_data.get("max_depth", 10),
                    follow_symlinks=scan_data.get("follow_symlinks", False),
                    skip_hidden=scan_data.get("skip_hidden", True),
                    batch_size=scan_data.get("batch_size", 100),
                    websocket=websocket,
                    progress_callback=send_progress,
                )
                
                # Send completion message
                await websocket.send_json({
                    "type": "scan_complete",
                    "data": {
                        "total_files": stats.total_files,
                        "total_dirs": stats.total_dirs,
                        "total_size": stats.total_size,
                        "scan_duration_ms": stats.scan_duration_ms,
                        "files_per_second": stats.files_per_second,
                    }
                })
            
            elif data.get("action") == "stop_scan":
                # TODO: Implement scan cancellation
                await websocket.send_json({
                    "type": "scan_stopped",
                    "message": "Scan stopped by user"
                })
            
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        active_connections.discard(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        active_connections.discard(websocket)


@router.get("/discover")
async def discover_files(
    root_path: str,
    return_list: bool = False,
) -> dict:
    """Fast file discovery without metadata.
    
    Args:
        root_path: Directory to scan
        return_list: If True, return file paths; if False, return count
        
    Returns:
        Dictionary with file count or list of paths
    """
    path = Path(root_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {root_path}")
    
    result = await scanner.discover_files(root_path, return_list)
    
    if return_list:
        return {"files": result, "count": len(result)}
    else:
        return {"count": result}


@router.post("/metadata")
async def extract_metadata(file_paths: list[str]) -> list[dict]:
    """Extract metadata for a batch of files.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        List of metadata dictionaries
    """
    if not file_paths:
        return []
    
    # Validate paths exist
    invalid_paths = [p for p in file_paths if not Path(p).exists()]
    if invalid_paths:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid paths: {invalid_paths[:5]}..."  # Show first 5
        )
    
    metadata_list = await scanner.extract_metadata_batch(file_paths)
    return [
        {
            "path": m.path,
            "filename": m.filename,
            "size": m.size,
            "modified": m.modified,
            "extension": m.extension,
        }
        for m in metadata_list
    ]


@router.post("/benchmark", response_model=dict)
async def benchmark_scan(request: BenchmarkRequest) -> dict:
    """Benchmark scanning performance.
    
    Args:
        request: Benchmark configuration
        
    Returns:
        Benchmark results
    """
    path = Path(request.root_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.root_path}")
    
    results = await scanner.benchmark_performance(
        root_path=request.root_path,
        iterations=request.iterations,
        warmup=request.warmup,
    )
    
    return results


@router.get("/system-info")
async def get_system_info() -> dict:
    """Get system information for performance tuning.
    
    Returns:
        System information dictionary
    """
    return scanner.get_system_info()


@router.get("/status")
async def get_scanner_status() -> dict:
    """Get current scanner status.
    
    Returns:
        Status information
    """
    return {
        "scanner_type": "zig_enhanced" if hasattr(scanner.zig_scanner, 'scan_music_directory_async') else "python_fallback",
        "active_connections": len(active_connections),
        "max_workers": scanner.executor._max_workers,
        "system_info": scanner.get_system_info(),
    }