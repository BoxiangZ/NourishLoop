from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.modules.catalog.models import MenuItem, NutritionFact, Venue


def list_venues(db: Session, limit: int = 50) -> list[Venue]:
    return list(db.scalars(select(Venue).order_by(Venue.name).limit(limit)))


def get_venue(db: Session, venue_id: str) -> Venue | None:
    return db.get(Venue, venue_id)


def list_menu_items(db: Session, venue_id: str | None = None, limit: int = 50):
    stmt = select(MenuItem, NutritionFact).join(NutritionFact).where(MenuItem.available.is_(True))
    if venue_id:
        stmt = stmt.where(MenuItem.venue_id == venue_id)
    return db.execute(stmt.order_by(MenuItem.name).limit(limit)).all()


def get_menu_item(db: Session, item_id: str):
    return db.execute(
        select(MenuItem, NutritionFact).join(NutritionFact).where(MenuItem.id == item_id)
    ).first()
