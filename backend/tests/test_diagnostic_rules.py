from app.diagnostic_rules import build_rule_based_diagnostic
from app.models import DiagnosticRequest, Difficulty, OperatingSystem, SelfServiceProbability


def test_data_risk_detects_disk_and_warns() -> None:
    request = DiagnosticRequest(
        operating_system=OperatingSystem.windows_11,
        issue_text="Mi laptop muestra BitLocker recovery key y no arranca después de un error SMART del SSD.",
        locale="es",
    )

    response = build_rule_based_diagnostic(request)

    assert response.difficulty == Difficulty.data_risk
    assert response.self_service_probability == SelfServiceProbability.low
    assert any("No formatees" in item or "No borres" in item for item in response.before_touching)
    assert "WhatsApp" not in response.whatsapp_prefill


def test_network_issue_gets_basic_steps() -> None:
    request = DiagnosticRequest(
        operating_system=OperatingSystem.windows_10,
        issue_text="El WiFi conecta pero no abre páginas web y parece error DNS en el navegador.",
        locale="es",
    )

    response = build_rule_based_diagnostic(request)

    assert response.difficulty == Difficulty.basic
    assert response.self_service_probability == SelfServiceProbability.high
    assert any("DNS" in step.title or "DNS" in step.detail for step in response.safe_steps)


def test_english_locale_returns_english_disclaimer() -> None:
    request = DiagnosticRequest(
        operating_system=OperatingSystem.macos,
        issue_text="The browser says proxy error and websites are not loading on Wi-Fi.",
        locale="en",
    )

    response = build_rule_based_diagnostic(request)

    assert "general technical guidance" in response.disclaimer
    assert response.summary.startswith("Initial triage")
