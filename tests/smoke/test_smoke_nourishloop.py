from __future__ import annotations

import os

import httpx
import pytest


@pytest.mark.smoke
def test_running_nourishloop_stack():
    base_url = os.environ.get("SMOKE_BASE_URL")
    if not base_url:
        pytest.skip("SMOKE_BASE_URL not set")
    with httpx.Client(base_url=base_url, timeout=10) as client:
        assert client.get("/api/v1/health").status_code == 200
        me = client.get("/api/v1/me")
        assert me.status_code == 200
        assert me.json()["id"] == "demo-student"
        menu = client.get("/api/v1/menu-items")
        assert menu.status_code == 200
        assert len(menu.json()) >= 1
        assert all(
            item["source_label"] == "NourishLoop fictional demo data" for item in menu.json()
        )
