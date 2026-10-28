from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from apps.api.core.config import Settings, get_settings
from apps.api.modules.tracking import async_review
from apps.api.modules.tracking.review import MealAIReview
from apps.api.modules.tracking.schemas import PhotoAnalysisRead, PhotoAutoEstimateRead, PhotoNutritionEstimateRead


def image_bytes() -> bytes:
    out = BytesIO()
    Image.new("RGB", (80, 80), "orange").save(out, format="JPEG")
    return out.getvalue()


def test_async_photo_review_updates_one_meal_with_source_nutrition(nl_stack, monkeypatch, tmp_path):
    client, session_factory = nl_stack
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    response = client.post("/api/v1/photo-meals/reviews", files={
        "photo": ("lunch.jpg", image_bytes(), "image/jpeg"),
    }, data={"notes": "One egg"})
    assert response.status_code == 202
    record = response.json()
    assert record["review_status"] == "pending"
    assert record["ai_review"] is None
    assert client.get("/api/v1/me/daily-summary").json()["meal_count"] == 0
    assert client.get(f"/api/v1/photo-meals/{record['id']}", headers={
        "X-Demo-User-Id": "demo-peer",
    }).status_code == 404

    review = MealAIReview(is_food=True, detected_foods=["Egg"], confidence=0.7,
                          estimated_nutrition={"calories_kcal": 90, "protein_g": 6,
                                               "carbs_g": 1, "fat_g": 7},
                          summary="One egg", assumptions=["Weight is estimated"])
    class Provider:
        def review(self, *_):
            return SimpleNamespace(review=review)

    monkeypatch.setattr(async_review, "auto_estimate_photo_nutrition", lambda *_:
        PhotoAutoEstimateRead(estimate=PhotoNutritionEstimateRead(
            nutrition={"calories_kcal": 98, "protein_g": 6.8, "carbs_g": 0.4, "fat_g": 7.4},
            items=[{"name": "Egg", "fdc_id": 173423, "source_description": "Egg, fried",
                    "source_url": "https://fdc.nal.usda.gov/food-search/?query=173423",
                    "grams": 50, "calories_kcal": 98, "protein_g": 6.8,
                    "carbs_g": 0.4, "fat_g": 7.4}],
        )))
    analyzer = lambda *_: PhotoAnalysisRead(foods=[{
        "name": "Egg", "preparation": "fried", "estimated_grams": 50,
    }], review_questions=[], model="test-vision")
    settings = Settings(upload_dir=str(tmp_path / "uploads"))
    assert async_review.process_photo_review_once(session_factory, settings,
        provider_factory=lambda _: Provider(), analyzer=analyzer) == record["id"]
    completed = client.get(f"/api/v1/photo-meals/{record['id']}").json()
    assert completed["review_status"] == "completed"
    assert completed["nutrition"]["calories_kcal"] == 98
    assert completed["ai_review"]["estimated_nutrition"]["calories_kcal"] == 90
    assert completed["review_attempts"] == 1
    assert "image_path" not in completed and "review_log" not in completed
    assert list((tmp_path / "uploads").iterdir()) == []
    assert async_review.process_photo_review_once(session_factory, settings,
        provider_factory=lambda _: Provider(), analyzer=analyzer) is None
    summary = client.get("/api/v1/me/daily-summary").json()
    assert summary["meal_count"] == 1
    assert summary["totals"]["calories_kcal"] == 98
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 5


def test_failed_review_can_retry_or_delete_without_counting(nl_stack, monkeypatch, tmp_path):
    client, session_factory = nl_stack
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    assert client.post("/api/v1/photo-meals/reviews", files={
        "photo": ("bad.jpg", b"not an image", "image/jpeg"),
    }).status_code == 422
    response = client.post("/api/v1/photo-meals/reviews", files={
        "photo": ("lunch.jpg", image_bytes(), "image/jpeg"),
    })
    record_id = response.json()["id"]
    class UnavailableProvider:
        def review(self, *_):
            raise RuntimeError("provider unavailable")

    settings = Settings(upload_dir=str(tmp_path / "uploads"))
    async_review.process_photo_review_once(session_factory, settings,
        provider_factory=lambda _: UnavailableProvider(),
        analyzer=lambda *_: (_ for _ in ()).throw(RuntimeError("unavailable")))
    failed = client.get(f"/api/v1/photo-meals/{record_id}").json()
    assert failed["review_status"] == "failed"
    assert failed["review_attempts"] == 1
    assert client.get("/api/v1/me/daily-summary").json()["meal_count"] == 0
    assert client.post(f"/api/v1/photo-meals/{record_id}/retry").status_code == 202
    assert client.delete(f"/api/v1/photo-meals/{record_id}", headers={
        "X-Demo-User-Id": "demo-peer",
    }).status_code == 404
    assert client.delete(f"/api/v1/photo-meals/{record_id}").status_code == 204
    assert not list(Path(settings.upload_dir).iterdir())


def test_ai_result_remains_visible_when_usda_recognition_is_unavailable(nl_stack, monkeypatch, tmp_path):
    client, session_factory = nl_stack
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    record_id = client.post("/api/v1/photo-meals/reviews", files={
        "photo": ("lunch.jpg", image_bytes(), "image/jpeg"),
    }).json()["id"]
    review = MealAIReview(is_food=True, detected_foods=["Rice bowl"], confidence=0.6,
                          estimated_nutrition={"calories_kcal": 420, "protein_g": 15,
                                               "carbs_g": 60, "fat_g": 12},
                          summary="A rice bowl", assumptions=["Portion is estimated"])
    class Provider:
        def review(self, *_):
            return SimpleNamespace(review=review)

    settings = Settings(upload_dir=str(tmp_path / "uploads"))
    async_review.process_photo_review_once(session_factory, settings,
        provider_factory=lambda _: Provider(),
        analyzer=lambda *_: (_ for _ in ()).throw(RuntimeError("USDA unavailable")))
    result = client.get(f"/api/v1/photo-meals/{record_id}").json()
    assert result["review_status"] == "completed"
    assert result["foods"][0]["name"] == "Rice bowl"
    assert result["ai_review"]["estimated_nutrition"]["calories_kcal"] == 420
    assert result["nutrition"] is None
    summary = client.get("/api/v1/me/daily-summary").json()
    assert summary["meal_count"] == 1
    assert summary["totals"]["calories_kcal"] == 0


def test_background_review_does_not_complete_without_any_nutrition(nl_stack, monkeypatch, tmp_path):
    client, session_factory = nl_stack
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    record_id = client.post("/api/v1/photo-meals/reviews", files={
        "photo": ("lunch.jpg", image_bytes(), "image/jpeg"),
    }).json()["id"]
    class UnavailableProvider:
        def review(self, *_):
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(async_review, "auto_estimate_photo_nutrition", lambda *_:
        PhotoAutoEstimateRead(estimate=None, partial_estimate=None, unresolved=["No match"]))
    async_review.process_photo_review_once(session_factory,
        Settings(upload_dir=str(tmp_path / "uploads")),
        provider_factory=lambda _: UnavailableProvider(),
        analyzer=lambda *_: PhotoAnalysisRead(foods=[{"name": "Rice"}], review_questions=[], model="test"))
    result = client.get(f"/api/v1/photo-meals/{record_id}").json()
    assert result["review_status"] == "failed"
    assert result["ai_review"] is None and result["nutrition"] is None
    assert client.get("/api/v1/me/daily-summary").json()["meal_count"] == 0
