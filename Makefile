.PHONY: install-dev up down reset test smoke migrate seed lint types

install-dev:
	pip install -e .[dev]

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

reset:
	docker compose down -v --remove-orphans

test:
	pytest -q tests/unit tests/integration

smoke:
	SMOKE_BASE_URL=http://localhost:8000 pytest -q tests/smoke/test_smoke_nourishloop.py

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose run --rm api python -m scripts.seed_nourishloop

lint:
	ruff check .

types:
	python -m scripts.generate_api_types
