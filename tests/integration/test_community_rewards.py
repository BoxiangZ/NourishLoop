from __future__ import annotations

import pytest
from sqlalchemy import event, func, select

from apps.api.core.config import get_settings
from apps.api.core.database import Base, make_engine, make_session_factory
from apps.api.core import import_models  # noqa: F401
from apps.api.modules.catalog.models import MenuItem, NutritionFact, Venue
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.models import CreditTransaction
from apps.api.seed import seed


def test_demo_seed_respects_foreign_keys_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()
    engine = make_engine(f"sqlite:///{tmp_path / 'seed-fk.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as db:
        seed(db)
        seed(db)
        assert db.scalar(select(func.count()).select_from(Venue)) == 2
        assert db.scalar(select(func.count()).select_from(MenuItem)) == 6
        assert db.scalar(select(func.count()).select_from(NutritionFact)) == 6
    engine.dispose()
    get_settings.cache_clear()


def confirm_meal(client, item_id: str, headers=None) -> str:
    plan = client.post("/api/v1/decisions", json={"menu_item_id": item_id}, headers=headers)
    assert plan.status_code == 201
    log = client.post(
        "/api/v1/meal-logs", json={"decision_id": plan.json()["id"]}, headers=headers
    )
    assert log.status_code == 201
    return log.json()["id"]


def test_habits_credits_redemption_and_share_reversal(nl_stack):
    client, session_factory = nl_stack
    item_id = client.get("/api/v1/menu-items").json()[0]["id"]
    initial = client.get("/api/v1/rewards/overview").json()
    assert initial["balance"] == 0
    assert all(not habit["completed_today"] for habit in initial["habits"])
    assert client.post("/api/v1/rewards/starter_badge/redeem").status_code == 409

    plan = client.post("/api/v1/decisions", json={"menu_item_id": item_id})
    assert plan.status_code == 201
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 0
    log = client.post("/api/v1/meal-logs", json={"decision_id": plan.json()["id"]})
    assert log.status_code == 201
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 5
    confirm_meal(client, item_id)
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 5

    post = client.post("/api/v1/community/posts", json={
        "meal_log_id": log.json()["id"], "caption": "Today's lunch",
    })
    assert post.status_code == 201
    post_id = post.json()["id"]
    assert client.get("/api/v1/community/me/shared-meal-log-ids").json() == [log.json()["id"]]
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 8
    assert client.post("/api/v1/community/posts", json={
        "meal_log_id": log.json()["id"], "caption": "Duplicate",
    }).status_code == 409
    assert client.put(f"/api/v1/community/posts/{post_id}/like").json()["like_count"] == 1
    assert client.put(f"/api/v1/community/posts/{post_id}/like").json()["like_count"] == 1
    assert client.delete(f"/api/v1/community/posts/{post_id}/like").json()["like_count"] == 0
    comment = client.post(f"/api/v1/community/posts/{post_id}/comments", json={
        "body": "Looks good",
    })
    assert comment.status_code == 201
    assert len(client.get("/api/v1/community/posts").json()[0]["comments"]) == 1
    assert client.delete(f"/api/v1/community/comments/{comment.json()['id']}").status_code == 204
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 8

    redeemed = client.post("/api/v1/rewards/starter_badge/redeem")
    assert redeemed.status_code == 201
    assert redeemed.json()["balance"] == 3
    assert client.post("/api/v1/rewards/starter_badge/redeem").status_code == 409
    assert client.delete(f"/api/v1/community/posts/{post_id}").status_code == 204
    assert client.get("/api/v1/community/posts").json() == []
    assert client.get("/api/v1/community/me/shared-meal-log-ids").json() == [log.json()["id"]]
    overview = client.get("/api/v1/rewards/overview").json()
    assert overview["balance"] == 0
    assert any(row["reason"] == "share_retracted" and row["amount"] == -3
               for row in overview["transactions"])
    share_habit = next(h for h in overview["habits"] if h["id"] == "share_meal")
    assert share_habit["completed_today"] is False
    assert next(r for r in overview["rewards"] if r["id"] == "starter_badge")["redeemed"] is True
    with session_factory() as db:
        assert db.get(User, "demo-student").is_moderator
        transaction = db.get(CreditTransaction, overview["transactions"][0]["id"])
        transaction.amount = 999
        with pytest.raises(ValueError, match="append-only"):
            db.commit()


def test_reporting_and_moderation_require_role(nl_stack):
    client, session_factory = nl_stack
    item_id = client.get("/api/v1/menu-items").json()[0]["id"]
    peer_headers = {"X-Demo-User-Id": "demo-peer"}
    assert client.get("/api/v1/me", headers=peer_headers).json()["is_moderator"] is False
    assert client.get("/api/v1/me", headers={"X-Demo-User-Id": "unknown"}).status_code == 403
    log_id = confirm_meal(client, item_id)
    post = client.post("/api/v1/community/posts", json={
        "meal_log_id": log_id, "caption": "Demo student's lunch",
    })
    assert post.status_code == 201
    post_id = post.json()["id"]
    assert client.get("/api/v1/community/reports/pending", headers=peer_headers).status_code == 403

    assert client.get("/api/v1/community/posts", headers=peer_headers).json()[0]["is_mine"] is False
    report = client.post(f"/api/v1/community/posts/{post_id}/reports", json={
        "reason": "misinformation", "detail": "Nutrition claim needs review",
    }, headers=peer_headers)
    assert report.status_code == 201
    assert client.post(f"/api/v1/community/posts/{post_id}/reports", json={
        "reason": "spam",
    }, headers=peer_headers).status_code == 409
    pending = client.get("/api/v1/community/reports/pending").json()
    assert len(pending) == 1
    resolved = client.post(f"/api/v1/community/reports/{report.json()['id']}/resolve", json={
        "action": "remove",
    })
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "removed"
    assert client.get("/api/v1/community/posts").json() == []
    assert client.get("/api/v1/community/reports/pending").json() == []
    with session_factory() as db:
        from apps.api.modules.rewards.service import credit_balance
        assert credit_balance(db, "demo-student") == 5
