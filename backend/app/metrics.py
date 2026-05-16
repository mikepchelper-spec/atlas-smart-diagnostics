from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Literal

from .models import DiagnosticRequest, DiagnosticResponse

MetricEvent = Literal["diagnosis", "whatsapp_click"]


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._events: Counter[str] = Counter()
        self._operating_systems: Counter[str] = Counter()
        self._categories: Counter[str] = Counter()
        self._difficulties: Counter[str] = Counter()
        self._locales: Counter[str] = Counter()

    def record_diagnosis(self, request: DiagnosticRequest, response: DiagnosticResponse) -> None:
        with self._lock:
            self._events["diagnosis"] += 1
            self._operating_systems[request.operating_system.value] += 1
            self._categories[_category_from_response(response)] += 1
            self._difficulties[response.difficulty.value] += 1
            self._locales[request.locale] += 1

    def record_event(self, event: MetricEvent) -> None:
        with self._lock:
            self._events[event] += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {
                "events": dict(self._events),
                "operating_systems": dict(self._operating_systems),
                "categories": dict(self._categories),
                "difficulties": dict(self._difficulties),
                "locales": dict(self._locales),
            }


def _category_from_response(response: DiagnosticResponse) -> str:
    combined = " ".join(cause.title.lower() for cause in response.likely_causes)
    if any(term in combined for term in ("disk", "boot", "bitlocker", "disco", "arranque", "datos")):
        return "data_risk"
    if any(term in combined for term in ("network", "dns", "router", "red")):
        return "network"
    if any(term in combined for term in ("printer", "spooler", "impres")):
        return "printer"
    if any(term in combined for term in ("driver", "update", "actualiz")):
        return "updates_drivers"
    return "general"


metrics_store = MetricsStore()
