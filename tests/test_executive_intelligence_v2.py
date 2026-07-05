from fastapi.testclient import TestClient

from backend.api import app


client = TestClient(app)


def test_v2_source_registry_endpoint() -> None:
    response = client.get("/v2/source-registry")
    assert response.status_code == 200
    body = response.json()
    assert "sources" in body
    assert "health" in body


def test_v2_dashboards_endpoint() -> None:
    response = client.get("/v2/executive/dashboards")
    assert response.status_code == 200
    body = response.json()
    assert "dashboards" in body


def test_v2_daily_brief_endpoint() -> None:
    response = client.get("/v2/executive/daily-brief")
    assert response.status_code == 200
    body = response.json()
    assert "top10Stories" in body
    assert "executiveActions" in body


def test_v2_search_endpoint() -> None:
    response = client.get("/v2/executive/search", params={"framework": "NIST"})
    assert response.status_code == 200
    body = response.json()
    assert "items" in body


def test_v2_scheduler_endpoint() -> None:
    response = client.get("/v2/executive/scheduler")
    assert response.status_code == 200
    body = response.json()
    assert "jobs" in body
    assert "runtime" in body
    assert "schedule" in body["runtime"]


def test_v2_pipeline_run_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.api.run_ingestion_enrichment_pipeline",
        lambda max_sources=None: {
            "source_count": 10,
            "attempted_sources": 10,
            "successful_sources": 8,
            "collected_items": 120,
            "deduplicated_items": 100,
            "inserted_records": 70,
            "updated_records": 20,
            "skipped_records": 10,
            "generated_at": "2026-01-01T00:00:00+00:00",
        },
    )
    response = client.post("/v2/executive/pipeline/run", params={"max_sources": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["source_count"] == 10
    assert body["deduplicated_items"] == 100
