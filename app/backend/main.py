from __future__ import annotations

import os
import signal
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

HOST = os.getenv("MT_SIDECAR_HOST", "127.0.0.1")
PORT = int(os.getenv("MT_SIDECAR_PORT", "5556"))

shutdown_event: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print(f"MT Sidecar starting on {HOST}:{PORT}", file=sys.stderr)
    yield
    print("MT Sidecar shutting down", file=sys.stderr)


app = FastAPI(title="MT Sidecar", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/shutdown")
async def shutdown() -> dict[str, str]:
    global shutdown_event
    shutdown_event = True
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting_down"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "mt-sidecar", "version": "0.1.0"}


def main() -> None:
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
