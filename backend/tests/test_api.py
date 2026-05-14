from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_diagnose_mock() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/diagnose",
        data={
            "operating_system": "windows_11",
            "issue_text": "Mi impresora no imprime y la cola de impresión se queda trabada.",
            "locale": "es",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["difficulty"] in {"basic", "intermediate", "advanced", "data_risk"}
    assert body["likely_causes"]
    assert body["model_provider"] == "mock"
