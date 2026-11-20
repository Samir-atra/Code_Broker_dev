"""Unit tests for the Bandit security scanning tool module."""

import asyncio
import os
from pathlib import Path
import pytest

from src.tools import security_scan


def test_security_scan_nonexistent_file():
    """Tests that providing a nonexistent file path returns an error."""
    result = asyncio.run(security_scan.get_security_score("/path/to/nonexistent_file.py"))
    assert "error" in result
    assert "Target path not found" in result["error"]


def test_security_scan_non_python_file(tmp_path):
    """Tests that a non-Python file returns a proper error message."""
    test_file = tmp_path / "notes.txt"
    test_file.write_text("just some text", encoding="utf-8")
    result = asyncio.run(security_scan.get_security_score(str(test_file)))
    assert "error" in result
    assert "Not a Python file" in result["error"]


def test_security_scan_valid_clean_python_file(tmp_path):
    """Tests scanning a clean Python file with zero security issues."""
    test_file = tmp_path / "clean_code.py"
    test_file.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    
    result = asyncio.run(security_scan.get_security_score(str(test_file)))
    assert "error" not in result
    assert result["security_score"] == 100.0
    assert result["total_issues"] == 0
    assert result["severity_counts"]["HIGH"] == 0
    assert Path(result["report_file"]).exists()


def test_security_scan_detects_insecure_code(tmp_path):
    """Tests scanning code with an intentional vulnerability (e.g., eval)."""
    test_file = tmp_path / "vulnerable_code.py"
    test_file.write_text("import os\neval('1 + 1')\n", encoding="utf-8")
    
    result = asyncio.run(security_scan.get_security_score(str(test_file)))
    assert "error" not in result
    assert result["total_issues"] >= 1
    # Security score should have been penalized from 100.0
    assert result["security_score"] < 100.0
    assert len(result["findings_summary"]) >= 1
