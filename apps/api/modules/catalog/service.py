from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.api.modules.catalog.models import ExternalNote, MenuItem, NutritionFact, Venue


def list_venues(
    db: Session, limit: int = 50, offset: int = 0, scope: str | None = None,
    query: str | None = None,
) -> list[Venue]:
    stmt = select(Venue)
    if scope:
        stmt = stmt.where(Venue.scope == scope)
    if query:
        pattern = f"%{query.strip()}%"
        stmt = stmt.where(or_(Venue.name.ilike(pattern), Venue.campus_area.ilike(pattern)))
    return list(db.scalars(stmt.order_by(Venue.name, Venue.id).offset(offset).limit(limit)))


def list_external_notes(db: Session, scope: str) -> list[ExternalNote]:
    return list(db.scalars(select(ExternalNote).where(ExternalNote.scope == scope)
                           .order_by(ExternalNote.title, ExternalNote.id)))


def get_venue(db: Session, venue_id: str) -> Venue | None:
    return db.get(Venue, venue_id)


def list_menu_items(
    db: Session, venue_id: str | None = None, limit: int = 50, offset: int = 0,
    query: str | None = None, tag: str | None = None, max_price_hkd: float | None = None,
):
    stmt = select(MenuItem, NutritionFact).join(NutritionFact).where(MenuItem.available.is_(True))
    if venue_id:
        stmt = stmt.where(MenuItem.venue_id == venue_id)
    if query:
        pattern = f"%{query.strip()}%"
        stmt = stmt.join(Venue).where(or_(
            MenuItem.name.ilike(pattern), MenuItem.description.ilike(pattern),
            Venue.name.ilike(pattern),
        ))
    if max_price_hkd is not None:
        stmt = stmt.where(MenuItem.price_hkd <= max_price_hkd)
    stmt = stmt.order_by(MenuItem.name, MenuItem.id)
    if tag:
        # The starter stores tags as JSON; filter before slicing on both SQLite and PostgreSQL.
        rows = [row for row in db.execute(stmt).all() if tag in row[0].tags]
        return rows[offset:offset + limit]
    return db.execute(stmt.offset(offset).limit(limit)).all()


def get_menu_item(db: Session, item_id: str):
    return db.execute(
        select(MenuItem, NutritionFact).join(NutritionFact).where(MenuItem.id == item_id)
    ).first()
