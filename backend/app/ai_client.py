from __future__ import annotations

import base64
import json
from typing import Any

import httpx
from pydantic import ValidationError

from .diagnostic_rules import build_rule_based_diagnostic
from .knowledge_base import knowledge_prompt
from .models import DiagnosticRequest, DiagnosticResponse
from .settings import Settings

SYSTEM_PROMPT = """
You are Atlas Smart Diagnostics, a cautious computer repair triage assistant.
Return only valid JSON matching the requested schema.
Prioritize safe, reversible steps. Never recommend formatting, deleting partitions,
registry edits, firmware flashing, diskpart clean, disabling security, or reinstalling
without explicit backup and risk warnings. If the case may involve data loss,
BitLocker, failing drives, malware/ransomware, or repeated boot failures, classify it
as data_risk and recommend professional support.
""".strip()


def _schema_hint() -> str:
    return json.dumps(DiagnosticResponse.model_json_schema(), ensure_ascii=False)


async def diagnose_with_ai(
    request: DiagnosticRequest,
    settings: Settings,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
) -> DiagnosticResponse:
    provider = settings.ai_provider.lower().strip()
    if provider == "mock" or not settings.ai_api_key:
        return build_rule_based_diagnostic(request, provider="mock")

    try:
        if provider in {"openai", "groq", "anthropic-compatible"}:
            return await _chat_completion(request, settings, image_bytes, image_mime)
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValidationError, ValueError):
        return build_rule_based_diagnostic(request, provider=f"{provider}-fallback")

    return build_rule_based_diagnostic(request, provider="unsupported-provider-fallback")


async def _chat_completion(
    request: DiagnosticRequest,
    settings: Settings,
    image_bytes: bytes | None,
    image_mime: str | None,
) -> DiagnosticResponse:
    base_url = _base_url(settings)
    model = _model(settings)
    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": _user_prompt(request, knowledge_prompt(request)),
        }
    ]
    if image_bytes and image_mime:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image_mime};base64,{encoded}"},
            }
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]

    parsed = json.loads(raw)
    parsed["model_provider"] = settings.ai_provider
    return DiagnosticResponse.model_validate(parsed)


def _base_url(settings: Settings) -> str:
    if settings.ai_base_url:
        return settings.ai_base_url.rstrip("/")
    if settings.ai_provider.lower() == "groq":
        return "https://api.groq.com/openai/v1"
    return "https://api.openai.com/v1"


def _model(settings: Settings) -> str:
    if settings.ai_model:
        return settings.ai_model
    if settings.ai_provider.lower() == "groq":
        return "meta-llama/llama-4-scout-17b-16e-instruct"
    return "gpt-4o-mini"


def _user_prompt(request: DiagnosticRequest, runbook_context: str) -> str:
    return f"""
Locale: {request.locale}
Operating system: {request.operating_system.value}
Linux distribution: {request.linux_distribution or ""}
Image provided: {request.image_provided}

{runbook_context}

User error/problem text:
{request.issue_text}

Return JSON following this schema. Keep language in the requested locale.
Schema: {_schema_hint()}
""".strip()
