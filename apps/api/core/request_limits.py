from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from apps.api.core.images import MAX_UPLOAD_REQUEST_BYTES


class _RequestBodyTooLarge(Exception):
    pass


def _error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={"error": {"code": "http_413", "message": message}},
    )


class MealPhotoBodyLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        path: str = "/api/v1/photo-meals/reviews",
        max_bytes: int = MAX_UPLOAD_REQUEST_BYTES,
    ):
        self.app = app
        self.path = path
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != self.path or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                await JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "http_400",
                            "message": "Invalid Content-Length header",
                        }
                    },
                )(scope, receive, send)
                return
            if declared_size > self.max_bytes:
                await _error_response("Image request must not exceed 8 MB")(
                    scope, receive, send
                )
                return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            await _error_response("Image request must not exceed 8 MB")(
                scope, receive, send
            )
