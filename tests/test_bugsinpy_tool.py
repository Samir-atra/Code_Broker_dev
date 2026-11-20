"""Unit tests for the BugsInPy test execution and test coverage assessment tool."""

import asyncio
from pathlib import Path
import pytest

from src.tools import bugsinpy_tool


def test_bugsinpy_tool_nonexistent_path():
    """Tests that providing a nonexistent path returns an error."""
    result = asyncio.run(bugsinpy_tool.get_test_score("/path/to/nonexistent_xyz.py"))
    assert "error" in result
    assert "Target path not found" in result["error"]


def test_bugsinpy_tool_no_tests_detected(tmp_path):
    """Tests that a codebase with no automated tests returns 0.0% test score."""
    code_file = tmp_path / "app.py"
    code_file.write_text("def run(): return 1\n", encoding="utf-8")

    result = asyncio.run(bugsinpy_tool.get_test_score(str(code_file)))
    assert "error" not in result
    assert result["has_tests"] is False
    assert result["test_score"] == 0.0
    assert "0.0%" in result["summary"]
    assert Path(result["report_file"]).exists()


def test_bugsinpy_tool_with_passing_tests(tmp_path):
    """Tests that discovering and executing passing unit tests returns 100.0% score."""
    code_file = tmp_path / "calculator.py"
    code_file.write_text("def add(a, b): return a + b\n", encoding="utf-8")

    test_file = tmp_path / "test_calculator.py"
    test_file.write_text(
        "from calculator import add\n\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n",
        encoding="utf-8"
    )

    result = asyncio.run(bugsinpy_tool.get_test_score(str(tmp_path)))
    assert "error" not in result
    assert result["has_tests"] is True
    assert result["test_score"] == 100.0
    assert result["tests_passed"] >= 1
    assert result["tests_failed"] == 0
    assert Path(result["report_file"]).exists()


def test_bugsinpy_framework_binary_lookup():
    """Tests locating bugsinpy-test and bugsinpy-info binaries."""
    info_bin = bugsinpy_tool._find_bugsinpy_bin("bugsinpy-info")
    assert info_bin is not None
    assert "bugsinpy-info" in info_bin
    assert Path(info_bin).exists()
