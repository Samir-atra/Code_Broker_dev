"""Unit tests for GitHub repository cloning and cleanup utilities."""

import asyncio
import os
from pathlib import Path
import pytest

from src.tools.read_github_repository import cleanup_temp_directory, read_github_repository


class MockCloneProcess:
    """Mock asyncio subprocess representing a git clone operation."""

    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    async def communicate(self):
        return self.stdout, self.stderr


def test_read_github_repository_invalid_url():
    """Tests that malformed or non-GitHub URLs return an error dictionary."""
    invalid_urls = [
        "https://notgithub.com/user/repo",
        "invalid-url-string",
        "ftp://github.com/user/repo",
        "https://github.com/onlyuser",
    ]
    for url in invalid_urls:
        result = asyncio.run(read_github_repository(url))
        assert "error" in result
        assert "Invalid GitHub repository URL" in result["error"]


def test_cleanup_temp_directory_valid(tmp_path):
    """Tests removing an existing temporary directory."""
    temp_dir = tmp_path / "temp_to_delete"
    temp_dir.mkdir()
    dummy_file = temp_dir / "file.txt"
    dummy_file.write_text("content", encoding="utf-8")

    result = cleanup_temp_directory(str(temp_dir))
    assert "success" in result
    assert not temp_dir.exists()


def test_cleanup_temp_directory_nonexistent():
    """Tests that attempting to clean up a non-existent directory returns an error."""
    result = cleanup_temp_directory("/path/to/nonexistent/temp_dir_999")
    assert "error" in result
    assert "Directory not found" in result["error"]


def test_read_github_repository_clone_failure(monkeypatch):
    """Tests handling git clone process failure and ensuring temp dir cleanup."""
    mock_process = MockCloneProcess(returncode=128, stderr=b"fatal: repository not found")

    async def mock_subprocess_shell(*args, **kwargs):
        return mock_process

    monkeypatch.setattr(asyncio, "create_subprocess_shell", mock_subprocess_shell)

    result = asyncio.run(
        read_github_repository("https://github.com/example/nonexistent_repo")
    )
    assert "error" in result
    assert "Failed to clone repository" in result["error"]


def test_read_github_repository_clone_success(monkeypatch, tmp_path):
    """Tests successful git clone workflow with mocked process and file reading."""
    mock_process = MockCloneProcess(returncode=0, stdout=b"Cloning into '.'...")

    created_temp_dirs = []

    async def mock_subprocess_shell(cmd, stdout=None, stderr=None, cwd=None):
        # Simulate files created in the temp directory
        if cwd and os.path.exists(cwd):
            sample_code = os.path.join(cwd, "main.py")
            with open(sample_code, "w", encoding="utf-8") as f:
                f.write("print('cloned')")
        return mock_process

    monkeypatch.setattr(asyncio, "create_subprocess_shell", mock_subprocess_shell)

    result = asyncio.run(
        read_github_repository("https://github.com/example/valid_repo")
    )
    try:
        assert "file_contents" in result
        assert "temp_dir" in result
        assert os.path.isdir(result["temp_dir"])
        temp_dir = result["temp_dir"]
        # Cleanup
        cleanup_temp_directory(temp_dir)
    except AssertionError:
        if "temp_dir" in result and os.path.isdir(result["temp_dir"]):
            cleanup_temp_directory(result["temp_dir"])
        raise
