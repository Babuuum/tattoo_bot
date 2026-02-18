from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MINIAPP_ROOT = _PROJECT_ROOT / "miniapp"
_MINIAPP_INDEX = _MINIAPP_ROOT / "index.html"
_MINIAPP_ASSETS_ROOT = _MINIAPP_ROOT / "public" / "assets"


@router.get("/miniapp", response_class=FileResponse)
async def miniapp_index() -> FileResponse:
    if not _MINIAPP_INDEX.exists():
        logger.error("Mini App index file is missing")
        raise HTTPException(status_code=404, detail="Mini App is not available")
    logger.info("Serving Mini App index")
    return FileResponse(_MINIAPP_INDEX)


@router.get("/assets/{asset_path:path}", response_class=FileResponse)
async def miniapp_asset(asset_path: str) -> FileResponse:
    candidate = (_MINIAPP_ASSETS_ROOT / asset_path).resolve()
    if not candidate.is_file():
        logger.warning("Mini App asset not found", extra={"asset_path": asset_path})
        raise HTTPException(status_code=404, detail="Asset not found")
    if _MINIAPP_ASSETS_ROOT.resolve() not in candidate.parents:
        logger.warning(
            "Rejected Mini App asset path traversal attempt",
            extra={"asset_path": asset_path},
        )
        raise HTTPException(status_code=404, detail="Asset not found")
    logger.info("Serving Mini App asset", extra={"asset_path": asset_path})
    return FileResponse(candidate)
