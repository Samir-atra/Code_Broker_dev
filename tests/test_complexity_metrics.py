"""Unit tests for the Radon complexity and maintainability metrics tool module."""

import asyncio
from pathlib import Path
import pytest

from src.tools import complexity_metrics


def test_complexity_metrics_nonexistent_file():
    """Tests that providing a nonexistent file path returns an error."""
    result = asyncio.run(complexity_metrics.get_complexity_score("/path/to/nonexistent_file.py"))
    assert "error" in result
    assert "Target path not found" in result["error"]


def test_complexity_metrics_non_python_file(tmp_path):
    """Tests that a non-Python file returns a proper error message."""
    test_file = tmp_path / "data.csv"
    test_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    result = asyncio.run(complexity_metrics.get_complexity_score(str(test_file)))
    assert "error" in result
    assert "Not a Python file" in result["error"]


def test_complexity_metrics_valid_python_file(tmp_path):
    """Tests analyzing a simple valid Python file for complexity metrics."""
    test_file = tmp_path / "math_ops.py"
    test_file.write_text(
        "def compute_sum(x: int, y: int) -> int:\n"
        "    \"\"\"Calculates sum.\"\"\"\n"
        "    return x + y\n\n"
        "def compute_product(x: int, y: int) -> int:\n"
        "    \"\"\"Calculates product.\"\"\"\n"
        "    return x * y\n",
        encoding="utf-8"
    )

    result = asyncio.run(complexity_metrics.get_complexity_score(str(test_file)))
    assert "error" not in result
    assert "maintainability_index" in result
    assert result["maintainability_index"] > 0.0
    assert result["maintainability_rank"] == "A"
    assert "average_complexity" in result
    assert result["complexity_rank"] == "A"
    assert result["complexity_score"] > 80.0
    assert result["analyzed_blocks_count"] == 2
    assert Path(result["report_file"]).exists()
