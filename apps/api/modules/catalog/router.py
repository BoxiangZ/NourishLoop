from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.core.config import get_settings
from apps.api.core.auth import current_user
from apps.api.modules.identity.models import User
from apps.api.modules.catalog.nutrition import search_nutrition_foods
from apps.api.modules.catalog.schemas import (
    ExternalNoteRead,
    MenuItemRead,
    NutritionFoodRead,
    VenueRead,
    menu_item_read,
)
from apps.api.modules.catalog.service import (
    get_menu_item,
    get_venue,
    list_external_notes,
    list_menu_items,
    list_venues,
)

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/nutrition-foods", response_model=list[NutritionFoodRead])
def nutrition_foods(
    q: str = Query(min_length=2, max_length=120),
    limit: int = Query(6, ge=1, le=20),
    _user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return search_nutrition_foods(db, q, limit, get_settings())


@router.get("/venues", response_model=list[VenueRead])
def venues(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    scope: str | None = Query(None, pattern="^(hkust|lohas|demo)$"),
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    return list_venues(db, limit, offset, scope, q)


@router.get("/external-notes", response_model=list[ExternalNoteRead])
def external_notes(
    scope: str = Query("hkust", pattern="^(hkust|lohas)$"),
    db: Session = Depends(get_db),
):
    return list_external_notes(db, scope)


@router.get("/venues/{venue_id}", response_model=VenueRead)
def venue(venue_id: str, db: Session = Depends(get_db)):
    result = get_venue(db, venue_id)
    if result is None:
        raise HTTPException(404, "Venue not found")
    return result


@router.get("/menu-items", response_model=list[MenuItemRead])
def menu_items(
    venue_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=100),
    tag: str | None = Query(None, max_length=40),
    max_price_hkd: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    return [
        menu_item_read(item, nutrition)
        for item, nutrition in list_menu_items(db, venue_id, limit, offset, q, tag, max_price_hkd)
    ]


@router.get("/menu-items/{item_id}", response_model=MenuItemRead)
def menu_item(item_id: str, db: Session = Depends(get_db)):
    result = get_menu_item(db, item_id)
    if result is None:
        raise HTTPException(404, "Menu item not found")
    return menu_item_read(*result)
