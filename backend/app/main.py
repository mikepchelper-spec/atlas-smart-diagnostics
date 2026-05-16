from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from .ai_client import diagnose_with_ai
from .case_id import generate_case_id
from .knowledge_base import knowledge_titles
from .metrics import metrics_store
from .models import DiagnosticRequest, DiagnosticResponse, OperatingSystem
from .settings import Settings, get_settings


app = FastAPI(
    title="Atlas Smart Diagnostics API",
    version="0.1.0",
    description="AI-assisted self-service computer diagnostic triage for Atlas PC Support.",
)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_request_times: dict[str, deque[float]] = defaultdict(deque)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/metrics")
def metrics(
    x_atlas_metrics_key: Annotated[str | None, Header(alias="X-Atlas-Metrics-Key")] = None,
    settings: Settings = Depends(get_settings),
) -> dict[str, dict[str, int]]:
    if not settings.metrics_admin_key or x_atlas_metrics_key != settings.metrics_admin_key:
        raise HTTPException(status_code=404, detail="Not found")
    return metrics_store.snapshot()


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
    response = await diagnose_with_ai(diagnostic_request, settings, image_bytes, image_mime)
    response = _prepare_handoff(response, diagnostic_request)
    metrics_store.record_diagnosis(diagnostic_request, response)
    return response


@app.post("/api/events/whatsapp-click")
def whatsapp_click() -> dict[str, str]:
    metrics_store.record_event("whatsapp_click")
    return {"status": "ok"}


def _prepare_handoff(response: DiagnosticResponse, request: DiagnosticRequest) -> DiagnosticResponse:
    case_id = generate_case_id()
    matches = knowledge_titles(request)
    response.case_id = case_id
    response.knowledge_matches = matches
    response.whatsapp_prefill = _structured_whatsapp(case_id, response, request)
    return response


def _structured_whatsapp(case_id: str, response: DiagnosticResponse, request: DiagnosticRequest) -> str:
    locale = request.locale
    os_label = request.linux_distribution if request.operating_system.value == "linux_other" and request.linux_distribution else request.operating_system.value
    top_cause = response.likely_causes[0].title if response.likely_causes else "Unknown"
    first_steps = "; ".join(step.title for step in response.safe_steps[:3])
    issue = " ".join(request.issue_text.split())
    if len(issue) > 220:
        issue = f"{issue[:219]}…"
    if locale == "en":
        return (
            f"Hello Atlas PC Support, I used Atlas Smart Diagnostics.\n"
            f"Case: {case_id}\n"
            f"OS: {os_label}\n"
            f"Difficulty: {response.difficulty.value}\n"
            f"Self-service probability: {response.self_service_probability.value}\n"
            f"Likely cause: {top_cause}\n"
            f"Suggested safe steps: {first_steps}\n"
            f"Problem: {issue}"
        )
    return (
        f"Hola Atlas PC Support, usé Atlas Smart Diagnostics.\n"
        f"Caso: {case_id}\n"
        f"Sistema: {os_label}\n"
        f"Dificultad: {response.difficulty.value}\n"
        f"Probabilidad autoservicio: {response.self_service_probability.value}\n"
        f"Causa probable: {top_cause}\n"
        f"Pasos seguros sugeridos: {first_steps}\n"
        f"Problema: {issue}"
    )


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
