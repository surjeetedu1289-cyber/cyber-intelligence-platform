from fastapi.testclient import TestClient

from backend.api import app


client = TestClient(app)


def test_health_and_collection_endpoints():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    news = client.get("/news")
    assert news.status_code == 200
    assert "items" in news.json()

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "requests" in metrics.json()
