from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
import re
from typing import NamedTuple

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.modules.catalog.models import NutritionFood
from apps.api.modules.catalog.schemas import NutritionFoodRead

NUTRIENTS = {
    "calories_kcal": 1008,
    "protein_g": 1003,
    "carbs_g": 1005,
    "fat_g": 1004,
}
INDEX_PATH = Path(__file__).resolve().parents[2] / "data/usda_sr_legacy_2018.csv"


class LocalFood(NamedTuple):
    fdc_id: int
    description: str
    calories_kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    tokens: frozenset[str]


def _word_tokens(value: str) -> frozenset[str]:
    words = re.findall(r"[a-z]+", value.lower())
    normalized = set()
    for word in words:
        if word.endswith("oes"):
            word = word[:-2]
        elif word.endswith("s") and not word.endswith(("ss", "ous", "us", "is")) and len(word) > 3:
            word = word[:-1]
        normalized.add(word)
    if "egg" in normalized:
        normalized.discard("chicken")
    normalized.difference_update({"shredded", "sliced", "chopped", "diced", "minced"})
    return frozenset(normalized)


def _first_subject(value: str) -> str | None:
    modifiers = {"cooked", "raw", "fried", "boiled", "steamed", "roasted", "baked",
                 "stir", "shredded", "sliced", "chopped", "diced", "minced"}
    for word in re.findall(r"[a-z]+", value.lower()):
        token = next(iter(_word_tokens(word)), None)
        if token and token not in modifiers:
            return token
    return None


@lru_cache(maxsize=1)
def _local_index() -> tuple[LocalFood, ...]:
    with INDEX_PATH.open(newline="") as source:
        return tuple(LocalFood(
            fdc_id=int(row["fdc_id"]), description=row["description"],
            calories_kcal=Decimal(row["calories_kcal"]),
            protein_g=Decimal(row["protein_g"]), carbs_g=Decimal(row["carbs_g"]),
            fat_g=Decimal(row["fat_g"]), tokens=_word_tokens(row["description"]),
        ) for row in csv.DictReader(source))


def _local_search(query: str, limit: int) -> list[LocalFood]:
    wanted = _word_tokens(query)
    if not wanted:
        return []
    matches = [food for food in _local_index() if wanted.issubset(food.tokens)]
    primary = _first_subject(query)
    def canonical_rank(food: LocalFood) -> int:
        if primary == "beef" and "ground" not in wanted:
            return 0 if {"composite", "all", "grade"}.issubset(food.tokens) else 1
        if primary == "tomato" and not {"green", "yellow", "orange", "red"} & wanted:
            return 0 if {"red", "ripe"}.issubset(food.tokens) else 1
        return 0
    matches.sort(key=lambda food: (
        _first_subject(food.description) != primary,
        canonical_rank(food),
        len(food.tokens - wanted), len(food.description), food.fdc_id,
    ))
    return matches[:limit]


def nutrition_food_read(food: NutritionFood) -> NutritionFoodRead:
    return NutritionFoodRead(
        fdc_id=food.fdc_id, description=food.description, data_type=food.data_type,
        calories_kcal=float(food.calories_kcal), protein_g=float(food.protein_g),
        carbs_g=float(food.carbs_g), fat_g=float(food.fat_g),
        source_url=f"https://fdc.nal.usda.gov/food-search/?query={food.fdc_id}",
    )


def _parse_food(data: dict) -> NutritionFood | None:
    if data.get("dataType") != "SR Legacy":
        return None
    try:
        values = {int(item["nutrientId"]): Decimal(str(item["value"]))
                  for item in data.get("foodNutrients", [])
                  if item.get("nutrientId") is not None and item.get("value") is not None}
        density = {key: values[nutrient_id] for key, nutrient_id in NUTRIENTS.items()}
        if any(not value.is_finite() or value < 0 or value > 2000
               for value in density.values()):
            return None
        fdc_id = int(data["fdcId"])
        description = str(data["description"]).strip()[:300]
        if not description or fdc_id <= 0:
            return None
    except (ValueError, KeyError, TypeError, InvalidOperation):
        return None
    return NutritionFood(
        fdc_id=fdc_id, description=description, data_type="SR Legacy",
        fetched_at=datetime.now(timezone.utc), **density,
    )


def search_nutrition_foods(
    db: Session, query: str, limit: int, settings: Settings,
    transport: httpx.BaseTransport | None = None,
    bypass_cache: bool = False,
) -> list[NutritionFoodRead]:
    query = query.strip()
    if not bypass_cache:
        local = _local_search(query, limit)
        if local:
            for food in local:
                db.merge(NutritionFood(
                    fdc_id=food.fdc_id, description=food.description, data_type="SR Legacy",
                    calories_kcal=food.calories_kcal, protein_g=food.protein_g,
                    carbs_g=food.carbs_g, fat_g=food.fat_g,
                    fetched_at=datetime.now(timezone.utc),
                ))
            db.commit()
            return [nutrition_food_read(db.get(NutritionFood, food.fdc_id)) for food in local]
    terms = re.findall(r"[A-Za-z]+", query)[:8]
    cached = db.scalars(select(NutritionFood).where(*[
        NutritionFood.description.ilike(f"%{term}%") for term in terms
    ]).order_by(NutritionFood.description).limit(limit)).all() if terms else []
    if cached and not bypass_cache:
        return [nutrition_food_read(food) for food in cached]
    try:
        with httpx.Client(timeout=settings.usda_timeout_seconds, transport=transport) as client:
            response = client.get("https://api.nal.usda.gov/fdc/v1/foods/search", params={
                "api_key": settings.usda_api_key.get_secret_value(),
                "query": query, "dataType": "SR Legacy", "pageSize": min(50, limit * 3),
            })
            response.raise_for_status()
            results = response.json().get("foods", [])
        foods = [_parse_food(item) for item in results]
        foods = [food for food in foods if food is not None]
        for food in foods:
            db.merge(food)
        db.commit()
        return [nutrition_food_read(food) for food in foods[:limit]]
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        raise HTTPException(503, "USDA food search is unavailable; try again later") from None
