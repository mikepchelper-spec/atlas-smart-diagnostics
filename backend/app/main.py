from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from .ai_client import diagnose_with_ai
from .models import DiagnosticRequest, DiagnosticResponse, OperatingSystem
from .settings import Settings, get_settings

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    yield


app = FastAPI(
    title="Atlas Smart Diagnostics API",
    version="0.1.0",
    description="AI-assisted self-service computer diagnostic triage for Atlas PC Support.",
    lifespan=lifespan,
)

_request_times: dict[str, deque[float]] = defaultdict(deque)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/diagnose", response_model=DiagnosticResponse)
async def diagnose(
    request: Request,
    operating_system: Annotated[OperatingSystem, Form()],
    issue_text: Annotated[str, Form(min_length=10, max_length=6000)],
    linux_distribution: Annotated[str | None, Form(max_length=80)] = None,
    locale: Annotated[str, Form(pattern="^(es|en)$")] = "es",
    image: Annotated[UploadFile | None, File()] = None,
    settings: Settings = Depends(get_settings),
) -> DiagnosticResponse:
    _rate_limit(request, settings)

    image_bytes: bytes | None = None
    image_mime: str | None = None
    if image and image.filename:
        image_bytes, image_mime = await _read_and_validate_image(image, settings)

    diagnostic_request = DiagnosticRequest(
        operating_system=operating_system,
        linux_distribution=linux_distribution,
        issue_text=issue_text,
        locale=locale,
        image_provided=bool(image_bytes),
    )
    return await diagnose_with_ai(diagnostic_request, settings, image_bytes, image_mime)


def _rate_limit(request: Request, settings: Settings) -> None:
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    bucket = _request_times[client_ip]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    bucket.append(now)


async def _read_and_validate_image(image: UploadFile, settings: Settings) -> tuple[bytes, str]:
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPG, PNG, and WebP images are supported.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await image.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Image is larger than {settings.max_upload_mb} MB.")
    try:
        with Image.open(__import__("io").BytesIO(data)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from exc
    return data, image.content_type or "image/jpeg"
