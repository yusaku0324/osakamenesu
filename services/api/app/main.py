from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings
import logging
from .meili import ensure_indexes
from .utils.ratelimit import create_rate_limiter, shutdown_rate_limiter
from .routers.profiles import router as profiles_router
from .routers.admin import router as admin_router
from .routers.shops import router as shops_router
from .routers.reservations import router as reservations_router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_session
from . import models
from redis.asyncio import from_url


app = FastAPI(title="Osaka Men-Esu API", version="0.1.0")

redis_client = from_url(settings.rate_limit_redis_url, encoding="utf-8", decode_responses=False) if settings.rate_limit_redis_url else None

# per token+ip: 5 requests / 10 seconds
_outlink_rate = create_rate_limiter(
    max_events=5,
    window_sec=10.0,
    redis_client=redis_client,
    namespace=settings.rate_limit_namespace,
    redis_error_cooldown=settings.rate_limit_redis_error_cooldown,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/api/out/{token}")
async def out_redirect(token: str, request: Request, db: AsyncSession = Depends(get_session)):
    """Resolve outlink token from DB and redirect. Optionally logs a click."""
    from fastapi.responses import RedirectResponse
    import hashlib

    res = await db.execute(select(models.Outlink).where(models.Outlink.token == token))
    ol = res.scalar_one_or_none()
    if not ol:
        raise HTTPException(status_code=404, detail="unknown token")

    # Rate limit per token+ip to mitigate abuse
    try:
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
        key = f"{token}:{ip}"
        allowed, retry_after = await _outlink_rate.allow(key)
        if not allowed:
            raise HTTPException(status_code=429, detail="too many requests")
        # Best-effort click logging (non-blocking)
        import hashlib
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else None
        referer = request.headers.get("referer")
        ua = request.headers.get("user-agent")
        click = models.Click(outlink_id=ol.id, referer=referer, ua=ua, ip_hash=ip_hash)
        db.add(click)
        await db.commit()
    except Exception:
        pass

    return RedirectResponse(ol.target_url, status_code=302)


@app.on_event("startup")
async def on_startup():
    logger = logging.getLogger("app.startup")
    # Initialize DB schema (dev convenience)
    if settings.init_db_on_startup:
        try:
            from .db import init_db
            await init_db()
        except Exception as e:
            logger.warning("DB init error: %s", e)
    # Ensure Meilisearch index/settings
    try:
        ensure_indexes()
    except Exception as e:
        logger.warning("Meili init error: %s", e)


app.include_router(profiles_router)
app.include_router(admin_router)
app.include_router(shops_router)
app.include_router(reservations_router)


@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_rate_limiter(_outlink_rate)
