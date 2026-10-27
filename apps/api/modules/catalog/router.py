from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.modules.catalog.schemas import MenuItemRead, VenueRead, menu_item_read
from apps.api.modules.catalog.service import get_menu_item, get_venue, list_menu_items, list_venues

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/venues", response_model=list[VenueRead])
def venues(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    return list_venues(db, limit)


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
    db: Session = Depends(get_db),
):
    return [
        menu_item_read(item, nutrition) for item, nutrition in list_menu_items(db, venue_id, limit)
    ]


@router.get("/menu-items/{item_id}", response_model=MenuItemRead)
def menu_item(item_id: str, db: Session = Depends(get_db)):
    result = get_menu_item(db, item_id)
    if result is None:
        raise HTTPException(404, "Menu item not found")
    return menu_item_read(*result)
