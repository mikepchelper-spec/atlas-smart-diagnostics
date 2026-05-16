from __future__ import annotations

import re
from dataclasses import dataclass

from .models import DiagnosticRequest


@dataclass(frozen=True)
class KnowledgeEntry:
    title: str
    tags: tuple[str, ...]
    summary_es: str
    summary_en: str


KNOWLEDGE_ENTRIES: tuple[KnowledgeEntry, ...] = (
    KnowledgeEntry(
        title="Atlas Printer Doctor",
        tags=("printer", "impresora", "spooler", "cola", "print"),
        summary_es="Revisar impresora predeterminada, trabajos trabados, estado del spooler, driver y conectividad antes de reinstalar.",
        summary_en="Check default printer, stuck jobs, spooler state, driver health, and connectivity before reinstalling.",
    ),
    KnowledgeEntry(
        title="Atlas GPU Slowness Triage",
        tags=("gpu", "graphics", "pantalla", "display", "driver", "whea", "video", "lento"),
        summary_es="Separar lentitud gráfica de fallas de disco/temperatura; revisar driver oficial, eventos WHEA concretos y uso de GPU.",
        summary_en="Separate graphics slowness from disk/thermal faults; check official drivers, specific WHEA events, and GPU usage.",
    ),
    KnowledgeEntry(
        title="Atlas AI Readiness Assessment",
        tags=("ai", "ia", "readiness", "ram", "cpu", "npu", "copilot"),
        summary_es="Evaluar CPU, RAM, almacenamiento, Windows y compatibilidad antes de recomendar flujos IA locales o cloud.",
        summary_en="Assess CPU, RAM, storage, Windows, and compatibility before recommending local or cloud AI workflows.",
    ),
    KnowledgeEntry(
        title="Atlas RustDesk Remote Support",
        tags=("rustdesk", "remote", "remoto", "relay", "id server", "soporte remoto"),
        summary_es="Para soporte remoto Atlas, confirmar ID/relay, conectividad y consentimiento antes de intervenir.",
        summary_en="For Atlas remote support, confirm ID/relay settings, connectivity, and user consent before intervening.",
    ),
    KnowledgeEntry(
        title="Atlas Backup First",
        tags=("backup", "respaldo", "bitlocker", "smart", "ssd", "hdd", "partition", "particion", "ransom"),
        summary_es="Si hay riesgo de datos, priorizar respaldo/imagen y evitar formateo, diskpart o reinstalación hasta proteger archivos.",
        summary_en="If data is at risk, prioritize backup/imaging and avoid formatting, diskpart, or reinstalling until files are protected.",
    ),
)


def find_knowledge(request: DiagnosticRequest, limit: int = 3) -> list[KnowledgeEntry]:
    text = f"{request.operating_system.value} {request.linux_distribution or ''} {request.issue_text}".lower()
    scored: list[tuple[int, KnowledgeEntry]] = []
    for entry in KNOWLEDGE_ENTRIES:
        score = sum(1 for tag in entry.tags if re.search(rf"\b{re.escape(tag)}\b", text))
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def knowledge_prompt(request: DiagnosticRequest) -> str:
    matches = find_knowledge(request)
    if not matches:
        return ""
    lines = []
    for entry in matches:
        summary = entry.summary_en if request.locale == "en" else entry.summary_es
        lines.append(f"- {entry.title}: {summary}")
    return "Atlas internal runbook hints:\n" + "\n".join(lines)


def knowledge_titles(request: DiagnosticRequest) -> list[str]:
    return [entry.title for entry in find_knowledge(request)]
