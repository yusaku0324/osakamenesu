from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .. import models
from ..db import get_session
from ..deps import require_user
from ..schemas import FavoriteCreate, FavoriteItem

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteItem])
async def list_favorites(
    user: models.User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    stmt = (
        select(models.UserFavorite)
        .where(models.UserFavorite.user_id == user.id)
        .order_by(models.UserFavorite.created_at.desc())
    )
    result = await db.execute(stmt)
    favorites = result.scalars().all()
    return [FavoriteItem(shop_id=f.shop_id, created_at=f.created_at) for f in favorites]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FavoriteItem)
async def add_favorite(
    payload: FavoriteCreate,
    user: models.User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    profile = await db.get(models.Profile, payload.shop_id)
    if not profile:
        raise HTTPException(status_code=404, detail="shop_not_found")

    favorite = models.UserFavorite(user_id=user.id, shop_id=payload.shop_id)
    db.add(favorite)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        stmt = select(models.UserFavorite).where(
            models.UserFavorite.user_id == user.id,
            models.UserFavorite.shop_id == payload.shop_id,
        )
        result = await db.execute(stmt)
        favorite = result.scalar_one()
    else:
        await db.refresh(favorite)

    return FavoriteItem(shop_id=favorite.shop_id, created_at=favorite.created_at)


@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    shop_id: UUID,
    user: models.User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    stmt = (
        delete(models.UserFavorite)
        .where(models.UserFavorite.user_id == user.id, models.UserFavorite.shop_id == shop_id)
    )
    await db.execute(stmt)
    await db.commit()
    return None
