from typing import Optional
from fastapi import Header, HTTPException, Depends, Request
from .settings import settings
from .db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from . import models
import hashlib


async def require_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="admin_not_configured")
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="unauthorized")


async def audit_admin(
    request: Request,
    db: AsyncSession = Depends(get_session),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
) -> None:
    try:
        # Compute ip hash like outlink logging
        ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else None
        key_hash = hashlib.sha256((x_admin_key or "").encode("utf-8")).hexdigest() if x_admin_key else None
        details = {
            "query": dict(request.query_params or {}),
            "path_params": dict(request.path_params or {}),
        }
        log = models.AdminLog(
            method=request.method,
            path=request.url.path,
            ip_hash=ip_hash,
            admin_key_hash=key_hash,
            details=details,
        )
        db.add(log)
        await db.commit()
    except Exception:
        # Best-effort; never block admin action
        pass
