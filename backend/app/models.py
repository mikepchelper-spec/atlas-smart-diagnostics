from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OperatingSystem(str, Enum):
    windows_10 = "windows_10"
    windows_11 = "windows_11"
    macos = "macos"
    linux_ubuntu = "linux_ubuntu"
    linux_debian = "linux_debian"
    linux_fedora = "linux_fedora"
    linux_mint = "linux_mint"
    linux_arch = "linux_arch"
    linux_other = "linux_other"


class Difficulty(str, Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    data_risk = "data_risk"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SelfServiceProbability(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Cause(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    explanation: str = Field(min_length=10, max_length=700)
    confidence: Confidence


class SafeStep(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    detail: str = Field(min_length=10, max_length=900)
    risk: Difficulty = Difficulty.basic


class StopSignal(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    detail: str = Field(min_length=10, max_length=700)


class DiagnosticRequest(BaseModel):
    operating_system: OperatingSystem
    linux_distribution: str | None = Field(default=None, max_length=80)
    issue_text: str = Field(min_length=10, max_length=6000)
    locale: str = Field(default="es", pattern="^(es|en)$")
    image_provided: bool = False


class DiagnosticResponse(BaseModel):
    case_id: str = Field(pattern=r"^ATLAS-CASE-[A-Z0-9]{6}$")
    summary: str = Field(min_length=10, max_length=600)
    likely_causes: list[Cause] = Field(min_length=1, max_length=5)
    difficulty: Difficulty
    self_service_probability: SelfServiceProbability
    risk_notice: str = Field(min_length=10, max_length=900)
    before_touching: list[str] = Field(min_length=2, max_length=6)
    safe_steps: list[SafeStep] = Field(min_length=1, max_length=8)
    stop_and_contact: list[StopSignal] = Field(min_length=1, max_length=6)
    customer_message: str = Field(min_length=20, max_length=1200)
    whatsapp_prefill: str = Field(min_length=20, max_length=1200)
    disclaimer: str = Field(min_length=20, max_length=1200)
    model_provider: str = Field(min_length=2, max_length=80)
    knowledge_matches: list[str] = Field(default_factory=list, max_length=5)
