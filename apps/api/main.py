from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.core.request_limits import MealPhotoBodyLimitMiddleware
from apps.api.core.database import get_db
from apps.api.core.import_models import catalog_models  # noqa: F401
from apps.api.core.schemas import ErrorResponse
from apps.api.modules.catalog.router import router as catalog_router
from apps.api.modules.community.router import router as community_router
from apps.api.modules.identity.router import router as identity_router
from apps.api.modules.recommendations.router import router as recommendations_router
from apps.api.modules.rewards.router import router as rewards_router
from apps.api.modules.tracking.router import router as tracking_router
from apps.api.modules.workouts.router import router as workouts_router


app = FastAPI(
    title="NourishLoop API",
    version="0.1.0",
    responses={status: {"model": ErrorResponse} for status in (404, 409, 422, 503)},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in get_settings().cors_origin.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Demo-User-Id"],
)
app.add_middleware(MealPhotoBodyLimitMiddleware)
app.include_router(identity_router)
app.include_router(catalog_router)
app.include_router(recommendations_router)
app.include_router(tracking_router)
app.include_router(community_router)
app.include_router(rewards_router)
app.include_router(workouts_router)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "Invalid request data"}},
    )


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
