from pathlib import Path

from fastapi.testclient import TestClient


def test_jobs_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_cleanup_endpoint_returns_counts(client: TestClient) -> None:
    response = client.post("/admin/cleanup?older_than_hours=24")
    assert response.status_code == 200
    payload = response.json()
    assert "deleted_jobs" in payload
    assert "stale_jobs_cleaned" in payload


def test_image_upload_rejects_unsupported_extension(client: TestClient, sample_text_file: Path) -> None:
    with sample_text_file.open("rb") as handle:
        response = client.post(
            "/image/jobs?target_format=PNG&quality=90",
            files={"file": ("sample.txt", handle, "text/plain")},
        )
    assert response.status_code == 400


def test_audio_upload_rejects_unsupported_extension(client: TestClient, sample_text_file: Path) -> None:
    with sample_text_file.open("rb") as handle:
        response = client.post(
            "/audio/jobs?target_format=MP3&bitrate=192k",
            files={"file": ("sample.txt", handle, "text/plain")},
        )
    assert response.status_code == 400


def test_video_upload_rejects_unsupported_extension(client: TestClient, sample_text_file: Path) -> None:
    with sample_text_file.open("rb") as handle:
        response = client.post(
            "/video/jobs?target_format=MP4&fps=0",
            files={"file": ("sample.txt", handle, "text/plain")},
        )
    assert response.status_code == 400


def test_document_upload_rejects_unsupported_extension(client: TestClient, sample_text_file: Path) -> None:
    with sample_text_file.open("rb") as handle:
        response = client.post(
            "/document/jobs?target_format=PDF",
            files={"file": ("sample.xyz", handle, "text/plain")},
        )
    assert response.status_code == 400


def test_batch_image_requires_files(client: TestClient) -> None:
    response = client.post("/batch/image/jobs?target_format=PNG&quality=90")
    assert response.status_code in {400, 422}


def test_batch_audio_requires_files(client: TestClient) -> None:
    response = client.post("/batch/audio/jobs?target_format=MP3&bitrate=192k")
    assert response.status_code in {400, 422}
