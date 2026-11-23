from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.api.modules.catalog.menu_locations import MENU_LOCATIONS, MenuLocation
from apps.api.modules.catalog.models import (
    ExternalNote, MenuItem, NutritionFact, PublishedDish, Venue,
)
from apps.api.modules.catalog.schemas import PublishedDishRead, VenueRead


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


def list_external_notes(db: Session, scope: str, limit: int, offset: int) -> list[ExternalNote]:
    stmt = select(ExternalNote)
    if scope != "all":
        stmt = stmt.where(ExternalNote.scope == scope)
    stmt = stmt.order_by(ExternalNote.source_checked_at.desc(), ExternalNote.title, ExternalNote.id)
    return list(db.scalars(stmt.offset(offset).limit(limit)))


def list_published_dishes(
    db: Session, limit: int, offset: int, scope: str | None, query: str | None,
    venue_id: str | None, location_id: str | None = None,
) -> list[PublishedDishRead]:
    stmt = select(PublishedDish, Venue).join(Venue).where(Venue.is_demo.is_(False))
    if scope:
        stmt = stmt.where(Venue.scope == scope)
    if venue_id:
        stmt = stmt.where(Venue.id == venue_id)
    if location_id:
        location = MENU_LOCATIONS.get(location_id)
        if location is None:
            raise HTTPException(404, "Menu location not found")
        stmt = stmt.where(Venue.scope == location.scope)
        if location.branches:
            stmt = stmt.where(Venue.name.in_(location.branches))
    if query:
        pattern = f"%{query.strip()}%"
        stmt = stmt.where(or_(PublishedDish.name.ilike(pattern), Venue.name.ilike(pattern),
                              Venue.campus_area.ilike(pattern)))
    rows = db.execute(stmt.order_by(PublishedDish.source_photo.is_(None), Venue.name,
                                   PublishedDish.name, PublishedDish.id)
                      .offset(offset).limit(limit))
    return [PublishedDishRead(
        id=dish.id, venue=VenueRead.model_validate(venue), name=dish.name,
        price_hkd=dish.price_hkd, source_url=dish.source_url, source_scope=dish.source_scope,
        reference_note=dish.reference_note, source_checked_at=dish.source_checked_at,
        source_photo=dish.source_photo,
    ) for dish, venue in rows]


def list_menu_locations(db: Session) -> list[MenuLocation]:
    locations_with_menus: dict[str, set[str]] = {}
    rows = db.execute(
        select(Venue.scope, Venue.name).join(PublishedDish)
        .where(Venue.is_demo.is_(False)).distinct()
    )
    for scope, branch in rows:
        locations_with_menus.setdefault(scope, set()).add(branch)
    return [
        location for location in MENU_LOCATIONS.values()
        if (branches := locations_with_menus.get(location.scope))
        and (not location.branches or branches.intersection(location.branches))
    ]


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
