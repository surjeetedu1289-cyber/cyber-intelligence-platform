from fastapi.testclient import TestClient

from backend.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "requests" in response.json()


def test_news_endpoint():
    response = client.get("/news")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_dashboard_endpoint():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "date" in response.json()
    assert "section_counts" in response.json()


def test_vendors_endpoint():
    response = client.get("/vendors")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_regulations_endpoint():
    response = client.get("/regulations")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_threats_endpoint():
    response = client.get("/threats")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_research_endpoint():
    response = client.get("/research")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_summary_endpoint():
    response = client.get("/summary")
    assert response.status_code in {200, 404}


def test_search_endpoint():
    response = client.get("/search", params={"q": "identity"})
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)
