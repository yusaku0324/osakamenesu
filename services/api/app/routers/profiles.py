from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from .. import models
from ..schemas import (
    ProfileCreate,
    ProfileDoc,
    ProfileDetail,
    AvailabilityOut,
)
from ..meili import index_profile, search as meili_search, build_filter
from ..utils.profiles import build_profile_doc, infer_height_age, infer_store_name
from ..deps import require_admin, audit_admin
from datetime import datetime
from zoneinfo import ZoneInfo


router = APIRouter()
JST = ZoneInfo("Asia/Tokyo")


def _to_doc(p: models.Profile, today: bool = False, tag_score: float = 0.0, ctr7d: float = 0.0) -> dict:
    """Compatibility wrapper to build a Meili doc from a Profile."""
    return ProfileDoc(**build_profile_doc(
        p,
        today=today,
        tag_score=tag_score,
        ctr7d=ctr7d,
    )).model_dump()


@router.post("/api/admin/profiles", summary="Create profile (seed)")
async def create_profile(payload: ProfileCreate, db: AsyncSession = Depends(get_session), _=Depends(require_admin), __=Depends(audit_admin)):
    p = models.Profile(
        name=payload.name,
        area=payload.area,
        price_min=payload.price_min,
        price_max=payload.price_max,
        bust_tag=payload.bust_tag,
        service_type=payload.service_type or 'store',
        height_cm=payload.height_cm,
        age=payload.age,
        body_tags=payload.body_tags,
        photos=payload.photos,
        contact_json=payload.contact_json,
        discounts=payload.discounts,
        ranking_badges=payload.ranking_badges,
        ranking_weight=payload.ranking_weight,
        status=payload.status,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    # index to Meili as published-only
    doc = _to_doc(p, today=False)
    index_profile(doc)
    return {"id": str(p.id)}


@router.get("/api/profiles/search")
async def search_profiles(q: str | None = None, area: str | None = None, bust: str | None = None,
                          service: str | None = None, body: str | None = None, page: int = 1, page_size: int = 12,
                          today: bool | None = None, price_min: int | None = None,
                          price_max: int | None = None, sort: str | None = None,
                          status: str | None = "published"):
    body_tags = [t for t in (body or "").split(",") if t]
    f = build_filter(area, bust, service, body_tags or None, today, price_min, price_max, status)
    # normalize sort (example: "price_min:asc") => "price_min:asc"
    sort_expr = None
    if sort:
        field, _, direction = sort.partition(":")
        sort_expr = f"{field}:{direction or 'asc'}"
    res = meili_search(
        q, f, sort_expr, max(1, page), max(1, min(page_size, 50)),
        facets=["area", "bust_tag", "service_type", "body_tags", "today"]
    )
    return {
        "page": page,
        "page_size": page_size,
        "total": res.get("estimatedTotalHits", 0),
        "hits": res.get("hits", []),
        "facets": res.get("facetDistribution", {}),
    }


@router.get("/api/profiles/{profile_id}", summary="Get profile detail")
async def get_profile_detail(profile_id: str, db: AsyncSession = Depends(get_session)):
    res = await db.execute(select(models.Profile).where(models.Profile.id == profile_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "profile not found")

    today = datetime.now(JST).date()
    # availability for today
    res_av = await db.execute(
        select(models.Availability)
        .where(models.Availability.profile_id == p.id, models.Availability.date == today)
        .limit(1)
    )
    av = res_av.scalar_one_or_none()
    av_out = None
    has_today = False
    if av:
        has_today = True
        av_out = AvailabilityOut(
            date=av.date.isoformat(), is_today=True, slots_json=av.slots_json or None
        )

    # outlinks
    res_ol = await db.execute(
        select(models.Outlink).where(models.Outlink.profile_id == p.id)
    )
    outlinks = list(res_ol.scalars().all())
    ol_list = [{"kind": o.kind, "token": o.token} for o in outlinks]

    # Common presentation attrs
    height_cm, age = infer_height_age(p)
    store_name = infer_store_name(p, outlinks)

    detail = ProfileDetail(
        id=str(p.id),
        name=p.name,
        area=p.area,
        price_min=p.price_min,
        price_max=p.price_max,
        bust_tag=p.bust_tag,
        service_type=p.service_type,
        body_tags=p.body_tags or [],
        height_cm=height_cm,
        age=age,
        photos=p.photos or [],
        discounts=p.discounts or [],
        ranking_badges=p.ranking_badges or [],
        ranking_weight=p.ranking_weight,
        status=p.status,
        store_name=store_name,
        today=has_today,
        availability_today=av_out,
        outlinks=ol_list,
    )
    return detail.model_dump()
