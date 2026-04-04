from fastapi.testclient import TestClient


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "phase-1"
