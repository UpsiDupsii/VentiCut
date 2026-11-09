from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "VentiCut" in data["message"]


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "VentiCut"


def test_create_and_get_job():
    create_resp = client.post(
        "/api/v1/clips/jobs",
        json={"target_aspect_ratio": "9:16", "max_duration_seconds": 60},
    )
    assert create_resp.status_code == 202
    job = create_resp.json()
    job_id = job["job_id"]
    assert job["status"] == "pending"

    get_resp = client.get(f"/api/v1/clips/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id
