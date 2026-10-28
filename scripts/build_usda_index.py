"""Build the compact USDA SR Legacy index used for offline nutrition lookup.

Source: https://fdc.nal.usda.gov/download-datasets/ (April 2018 CSV archive).
Run: python -m scripts.build_usda_index /path/to/FoodData_Central_sr_legacy_food_csv_2018-04.zip
"""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from pathlib import Path


NUTRIENTS = {1008: "calories_kcal", 1003: "protein_g", 1005: "carbs_g", 1004: "fat_g"}
OUTPUT = Path(__file__).resolve().parents[1] / "apps/api/data/usda_sr_legacy_2018.csv"


def _rows(archive: zipfile.ZipFile, basename: str):
    name = next(name for name in archive.namelist() if name.endswith("/" + basename))
    with archive.open(name) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def build(archive_path: Path, output_path: Path = OUTPUT) -> int:
    with zipfile.ZipFile(archive_path) as archive:
        descriptions = {
            int(row["fdc_id"]): row["description"]
            for row in _rows(archive, "food.csv")
            if row["data_type"] == "sr_legacy_food"
        }
        values: dict[int, dict[str, str]] = {}
        for row in _rows(archive, "food_nutrient.csv"):
            fdc_id = int(row["fdc_id"])
            nutrient = NUTRIENTS.get(int(row["nutrient_id"]))
            if fdc_id in descriptions and nutrient and row["amount"]:
                values.setdefault(fdc_id, {})[nutrient] = row["amount"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(("fdc_id", "description", *NUTRIENTS.values()))
        count = 0
        for fdc_id, description in sorted(descriptions.items()):
            nutrients = values.get(fdc_id, {})
            if len(nutrients) != len(NUTRIENTS):
                continue
            writer.writerow((fdc_id, description, *(nutrients[key] for key in NUTRIENTS.values())))
            count += 1
    return count


if __name__ == "__main__":
    count = build(Path(sys.argv[1]))
    print(f"Wrote {count} source-backed foods to {OUTPUT}")
