"""API tests for files endpoints."""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app
from utils.database import init_database, get_db_connection, get_storage_path


@pytest.fixture
def test_client():
    """Create test client with temporary database."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Patch paths
    with patch("utils.database.DEFAULT_DB_PATH", db_path):
        with patch("utils.database.DEFAULT_STORAGE_PATH", docs_dir):
            with patch("services.file_service.DEFAULT_DB_PATH", db_path):
                with patch("services.file_service.DEFAULT_STORAGE_PATH", docs_dir):
                    init_database(db_path)

                    # Create test client
                    client = TestClient(app)

                    yield {
                        "client": client,
                        "temp_dir": temp_dir,
                        "db_path": db_path,
                        "docs_dir": docs_dir,
                    }

    shutil.rmtree(temp_dir)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, test_client):
        """Test health endpoint returns OK."""
        response = test_client["client"].get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "knowledge-base"


class TestFileTreeEndpoint:
    """Tests for file tree endpoint."""

    def test_get_empty_tree(self, test_client):
        """Test empty tree returns empty list."""
        response = test_client["client"].get("/api/files/tree")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"] == []

    def test_get_tree_with_files(self, test_client):
        """Test tree with files returns proper structure."""
        client = test_client["client"]

        # Upload a file
        files = {"file": ("test.txt", b"content", "text/plain")}
        client.post("/api/files/upload", files=files)

        # Get tree
        response = client.get("/api/files/tree")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1


class TestUploadEndpoint:
    """Tests for file upload endpoint."""

    def test_upload_text_file(self, test_client):
        """Test uploading a text file."""
        files = {"file": ("test.txt", b"Test content", "text/plain")}
        response = test_client["client"].post("/api/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["name"] == "test.txt"
        assert data["data"]["type"] == "text"
        assert data["data"]["size"] == 12

    def test_upload_pdf_file(self, test_client):
        """Test uploading a PDF file."""
        files = {"file": ("document.pdf", b"%PDF-1.4 content", "application/pdf")}
        response = test_client["client"].post("/api/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["type"] == "pdf"

    def test_upload_with_parent_id(self, test_client):
        """Test uploading file to specific folder."""
        client = test_client["client"]

        # Create folder first
        folder_response = client.post(
            "/api/files/folder",
            json={"name": "my_folder"}
        )
        folder_id = folder_response.json()["data"]["id"]

        # Upload to folder
        files = {"file": ("nested.txt", b"content", "text/plain")}
        data = {"parent_id": folder_id}
        response = client.post(
            "/api/files/upload",
            files=files,
            data=data
        )

        assert response.status_code == 200
        file_data = response.json()["data"]
        assert "/my_folder/nested.txt" in file_data["path"]

    def test_upload_duplicate_name(self, test_client):
        """Test uploading file with duplicate name."""
        client = test_client["client"]

        # Upload first file
        files1 = {"file": ("duplicate.txt", b"first", "text/plain")}
        client.post("/api/files/upload", files=files1)

        # Upload second with same name
        files2 = {"file": ("duplicate.txt", b"second", "text/plain")}
        response = client.post("/api/files/upload", files=files2)

        assert response.status_code == 200
        data = response.json()
        assert "duplicate (1).txt" in data["data"]["name"]


class TestFileDetailEndpoint:
    """Tests for file detail endpoint."""

    def test_get_file_detail(self, test_client):
        """Test getting file detail."""
        client = test_client["client"]

        # Upload file
        files = {"file": ("detail.txt", b"content", "text/plain")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["data"]["id"]

        # Get detail
        response = client.get(f"/api/files/{file_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == file_id
        assert data["data"]["mimeType"] == "text/plain"

    def test_get_nonexistent_file(self, test_client):
        """Test getting nonexistent file returns 404."""
        response = test_client["client"].get("/api/files/nonexistent-id")
        assert response.status_code == 404


class TestCreateFolderEndpoint:
    """Tests for folder creation endpoint."""

    def test_create_folder_root(self, test_client):
        """Test creating folder in root."""
        response = test_client["client"].post(
            "/api/files/folder",
            json={"name": "新文件夹"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["name"] == "新文件夹"
        assert data["data"]["isFolder"] is True

    def test_create_nested_folder(self, test_client):
        """Test creating nested folder."""
        client = test_client["client"]

        # Create parent folder
        parent_response = client.post(
            "/api/files/folder",
            json={"name": "parent"}
        )
        parent_id = parent_response.json()["data"]["id"]

        # Create child folder
        child_response = client.post(
            "/api/files/folder",
            json={"name": "child", "parent_id": parent_id}
        )

        assert child_response.status_code == 200
        child_data = child_response.json()["data"]
        assert "/parent/child" in child_data["path"]

    def test_create_duplicate_folder(self, test_client):
        """Test creating folder with duplicate name."""
        client = test_client["client"]

        # Create first folder
        client.post("/api/files/folder", json={"name": "duplicate"})

        # Create second with same name
        response = client.post("/api/files/folder", json={"name": "duplicate"})

        assert response.status_code == 200
        data = response.json()
        assert "duplicate (1)" in data["data"]["name"]


class TestMoveFileEndpoint:
    """Tests for file move endpoint."""

    def test_move_file_to_folder(self, test_client):
        """Test moving file to folder."""
        client = test_client["client"]

        # Create folder and file
        folder_response = client.post("/api/files/folder", json={"name": "destination"})
        folder_id = folder_response.json()["data"]["id"]

        files = {"file": ("to_move.txt", b"content", "text/plain")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["data"]["id"]

        # Move file
        move_response = client.post(
            "/api/files/move",
            json={"file_id": file_id, "target_folder_id": folder_id}
        )

        assert move_response.status_code == 200
        data = move_response.json()
        assert "/destination/to_move.txt" in data["data"]["path"]

    def test_move_file_to_root(self, test_client):
        """Test moving file to root."""
        client = test_client["client"]

        # Create folder, then file inside
        folder_response = client.post("/api/files/folder", json={"name": "source"})
        folder_id = folder_response.json()["data"]["id"]

        files = {"file": ("in_folder.txt", b"content", "text/plain")}
        data = {"parent_id": folder_id}
        upload_response = client.post("/api/files/upload", files=files, data=data)
        file_id = upload_response.json()["data"]["id"]

        # Move to root
        move_response = client.post(
            "/api/files/move",
            json={"file_id": file_id, "target_folder_id": None}
        )

        assert move_response.status_code == 200
        move_data = move_response.json()
        assert move_data["data"]["path"] == "/docs/in_folder.txt"

    def test_move_nonexistent_file(self, test_client):
        """Test moving nonexistent file returns 404."""
        response = test_client["client"].post(
            "/api/files/move",
            json={"file_id": "nonexistent", "target_folder_id": None}
        )
        assert response.status_code == 404

    def test_move_to_nonexistent_folder(self, test_client):
        """Test moving to nonexistent folder returns error."""
        client = test_client["client"]

        # Upload file
        files = {"file": ("test.txt", b"content", "text/plain")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["data"]["id"]

        # Try to move to nonexistent folder
        move_response = client.post(
            "/api/files/move",
            json={"file_id": file_id, "target_folder_id": "nonexistent-folder"}
        )
        assert move_response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])