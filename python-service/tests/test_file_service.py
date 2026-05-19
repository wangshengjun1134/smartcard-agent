"""Unit tests for FileService."""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.file import FileType, detect_file_type, get_mime_type
from utils.database import init_database, get_db_connection


class TestFileTypeDetection:
    """Tests for file type detection."""

    def test_detect_pdf(self):
        """Test PDF file detection."""
        assert detect_file_type("document.pdf") == FileType.PDF
        assert detect_file_type("DOCUMENT.PDF") == FileType.PDF

    def test_detect_word(self):
        """Test Word file detection."""
        assert detect_file_type("document.doc") == FileType.WORD
        assert detect_file_type("document.docx") == FileType.WORD

    def test_detect_markdown(self):
        """Test Markdown file detection."""
        assert detect_file_type("README.md") == FileType.MARKDOWN
        assert detect_file_type("notes.markdown") == FileType.MARKDOWN

    def test_detect_text(self):
        """Test text file detection."""
        assert detect_file_type("notes.txt") == FileType.TEXT

    def test_detect_image(self):
        """Test image file detection."""
        assert detect_file_type("photo.png") == FileType.IMAGE
        assert detect_file_type("photo.jpg") == FileType.IMAGE
        assert detect_file_type("photo.jpeg") == FileType.IMAGE
        assert detect_file_type("photo.gif") == FileType.IMAGE
        assert detect_file_type("photo.webp") == FileType.IMAGE

    def test_detect_unknown(self):
        """Test unknown file type detection."""
        assert detect_file_type("archive.zip") == FileType.UNKNOWN
        assert detect_file_type("data.bin") == FileType.UNKNOWN
        assert detect_file_type("") == FileType.UNKNOWN


class TestMimeType:
    """Tests for MIME type detection."""

    def test_mime_pdf(self):
        """Test PDF MIME type."""
        assert get_mime_type("doc.pdf", FileType.PDF) == "application/pdf"

    def test_mime_markdown(self):
        """Test Markdown MIME type."""
        assert get_mime_type("README.md", FileType.MARKDOWN) == "text/markdown"

    def test_mime_text(self):
        """Test text MIME type."""
        assert get_mime_type("notes.txt", FileType.TEXT) == "text/plain"

    def test_mime_folder(self):
        """Test folder MIME type."""
        assert get_mime_type("folder", FileType.FOLDER) == "inode/directory"

    def test_mime_image(self):
        """Test image MIME type detection."""
        assert get_mime_type("photo.png", FileType.IMAGE) == "image/png"
        assert get_mime_type("photo.jpg", FileType.IMAGE) == "image/jpeg"
        assert get_mime_type("photo.gif", FileType.IMAGE) == "image/gif"


class TestDatabase:
    """Tests for database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_knowledge.db"
        init_database(db_path)
        yield db_path
        shutil.rmtree(temp_dir)

    def test_database_creation(self, temp_db):
        """Test database is created correctly."""
        assert temp_db.exists()

    def test_tables_exist(self, temp_db):
        """Test files table exists."""
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "files" in tables

    def test_indexes_exist(self, temp_db):
        """Test indexes are created."""
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "idx_files_parent_id" in indexes
        assert "idx_files_name" in indexes
        assert "idx_files_status" in indexes

    def test_wal_mode(self, temp_db):
        """Test WAL mode is enabled."""
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        conn.close()

        assert mode.lower() == "wal"


class TestFileServicePath:
    """Tests for path generation and sanitization."""

    @pytest.fixture
    def temp_env(self):
        """Create temporary environment for testing."""
        temp_dir = tempfile.mkdtemp()
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        db_path = Path(temp_dir) / "test.db"

        # Patch the default paths
        with patch("utils.database.DEFAULT_DB_PATH", db_path):
            with patch("utils.database.DEFAULT_STORAGE_PATH", docs_dir):
                with patch("services.file_service.DEFAULT_DB_PATH", db_path):
                    with patch("services.file_service.DEFAULT_STORAGE_PATH", docs_dir):
                        init_database(db_path)
                        yield {
                            "temp_dir": temp_dir,
                            "docs_dir": docs_dir,
                            "db_path": db_path,
                        }

        shutil.rmtree(temp_dir)

    def test_sanitize_name_basic(self, temp_env):
        """Test basic name sanitization."""
        from services.file_service import FileService

        service = FileService()
        assert service._sanitize_name("valid_name.txt") == "valid_name.txt"
        assert service._sanitize_name("测试文件.pdf") == "测试文件.pdf"

    def test_sanitize_name_invalid_chars(self, temp_env):
        """Test invalid characters are removed."""
        from services.file_service import FileService

        service = FileService()
        assert service._sanitize_name("file/name.txt") == "file_name.txt"
        assert service._sanitize_name("file\\name.txt") == "file_name.txt"
        assert service._sanitize_name("file:name.txt") == "file_name.txt"
        assert service._sanitize_name("file*name.txt") == "file_name.txt"

    def test_sanitize_name_empty(self, temp_env):
        """Test empty name handling."""
        from services.file_service import FileService

        service = FileService()
        assert service._sanitize_name("") == "unnamed"
        assert service._sanitize_name("...") == "unnamed"

    def test_resolve_name_conflict_no_conflict(self, temp_env):
        """Test no conflict returns original name."""
        from services.file_service import FileService

        service = FileService()
        result = service._resolve_name_conflict(None, "unique.txt")
        assert result == "unique.txt"

    def test_resolve_name_conflict_with_conflict(self, temp_env):
        """Test conflict adds number."""
        from services.file_service import FileService

        service = FileService()

        # Insert a file first
        conn = get_db_connection(temp_env["db_path"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (id, name, parent_id, is_folder, file_type, created_at, modified_at) VALUES (?, ?, NULL, 0, 'text', ?, ?)",
            ("test-id-1", "existing.txt", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z")
        )
        conn.commit()
        conn.close()

        result = service._resolve_name_conflict(None, "existing.txt")
        assert result == "existing (1).txt"


class TestFileServiceOperations:
    """Tests for file service operations."""

    @pytest.fixture
    async def temp_env(self):
        """Create temporary environment for async testing."""
        temp_dir = tempfile.mkdtemp()
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        db_path = Path(temp_dir) / "test.db"

        with patch("utils.database.DEFAULT_DB_PATH", db_path):
            with patch("utils.database.DEFAULT_STORAGE_PATH", docs_dir):
                with patch("services.file_service.DEFAULT_DB_PATH", db_path):
                    with patch("services.file_service.DEFAULT_STORAGE_PATH", docs_dir):
                        init_database(db_path)
                        yield {
                            "temp_dir": temp_dir,
                            "docs_dir": docs_dir,
                            "db_path": db_path,
                        }

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_create_folder(self, temp_env):
        """Test folder creation."""
        from services.file_service import FileService

        service = FileService()
        folder = await service.create_folder("测试文件夹")

        assert folder is not None
        assert folder.name == "测试文件夹"
        assert folder.isFolder is True
        assert folder.type == FileType.FOLDER

        # Check database
        conn = get_db_connection(temp_env["db_path"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (folder.id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["name"] == "测试文件夹"

    @pytest.mark.asyncio
    async def test_upload_file(self, temp_env):
        """Test file upload."""
        from services.file_service import FileService

        service = FileService()
        content = b"Test file content"
        file_node = await service.upload_file(content, "test.txt")

        assert file_node is not None
        assert file_node.name == "test.txt"
        assert file_node.type == FileType.TEXT
        assert file_node.size == len(content)

        # Check file exists on disk
        disk_path = temp_env["docs_dir"] / "test.txt"
        assert disk_path.exists()
        assert disk_path.read_bytes() == content

    @pytest.mark.asyncio
    async def test_get_file_tree(self, temp_env):
        """Test file tree retrieval."""
        from services.file_service import FileService

        service = FileService()

        # Create some files
        await service.create_folder("folder1")
        file_node = await service.upload_file(b"content", "file1.txt")

        tree = service.get_file_tree()

        assert len(tree) >= 2  # At least folder and file

    @pytest.mark.asyncio
    async def test_move_file(self, temp_env):
        """Test file move operation."""
        from services.file_service import FileService

        service = FileService()

        # Create folder and file
        folder = await service.create_folder("target_folder")
        file_node = await service.upload_file(b"content", "move_me.txt")

        # Move file to folder
        moved = await service.move_file(file_node.id, folder.id)

        assert moved is not None
        assert "/target_folder/move_me.txt" in moved.path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])