FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1 \
PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY services /app/services
COPY apps/api /app/apps/api
COPY apps/__init__.py /app/apps/__init__.py
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
RUN pip install --upgrade pip && pip install -e ".[dev]"
COPY tests /app/tests
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
