from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")
    return file_path
