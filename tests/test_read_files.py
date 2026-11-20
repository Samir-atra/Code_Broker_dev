"""Unit tests for the file reading utilities in src/tools/read_files.py."""

import os
from pathlib import Path
import pytest

from src.tools.read_files import read_directory_files, read_file


def test_read_file_existing(tmp_path):
    """Tests reading an existing text file."""
    sample_file = tmp_path / "sample.py"
    sample_file.write_text("x = 42\nprint(x)\n", encoding="utf-8")

    content = read_file(str(sample_file))
    assert "x = 42" in content
    assert "print(x)" in content


def test_read_file_nonexistent():
    """Tests reading a file that does not exist returns an error message."""
    content = read_file("/path/to/nonexistent/file_xyz.py")
    assert content.startswith("Error: File not found")


def test_read_file_empty(tmp_path):
    """Tests reading an empty file returns an empty string."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    content = read_file(str(empty_file))
    assert content == ""


def test_read_file_unicode_characters(tmp_path):
    """Tests reading files containing multi-byte UTF-8 characters."""
    unicode_file = tmp_path / "unicode.py"
    unicode_file.write_text("# 🐍 🚀 测试 Unicode\n", encoding="utf-8")

    content = read_file(str(unicode_file))
    assert "🐍 🚀 测试 Unicode" in content


def test_read_directory_files_valid(tmp_path):
    """Tests reading all files in a directory and its subdirectories."""
    file1 = tmp_path / "mod1.py"
    file1.write_text("def fn1(): pass", encoding="utf-8")

    sub_dir = tmp_path / "pkg"
    sub_dir.mkdir()
    file2 = sub_dir / "mod2.py"
    file2.write_text("def fn2(): pass", encoding="utf-8")

    result = read_directory_files(str(tmp_path))
    assert str(file1) in result
    assert str(file2) in result
    assert "def fn1(): pass" in result[str(file1)]
    assert "def fn2(): pass" in result[str(file2)]


def test_read_directory_files_skips_git_directory(tmp_path):
    """Tests that files inside a .git directory are strictly excluded."""
    regular_file = tmp_path / "main.py"
    regular_file.write_text("print('hello')", encoding="utf-8")

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    git_file = git_dir / "config"
    git_file.write_text("[core]\nrepositoryformatversion = 0", encoding="utf-8")

    result = read_directory_files(str(tmp_path))
    assert str(regular_file) in result
    assert str(git_file) not in result


def test_read_directory_files_nonexistent():
    """Tests that passing a non-existent directory returns an error dictionary."""
    result = read_directory_files("/path/to/nonexistent_dir_123")
    assert "error" in result
    assert "Directory not found" in result["error"]
