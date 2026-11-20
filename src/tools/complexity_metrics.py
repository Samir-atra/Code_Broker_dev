"""Code complexity and maintainability metrics tool module.

This module provides utility functions to run Radon analysis (Cyclomatic
Complexity and Maintainability Index) on target Python files or directories,
save the complete output to a report file, and compute objective scores.
"""

import asyncio
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

RADON_TIMEOUT_SECONDS = 60


def _get_reports_dir() -> Path:
    """Finds or creates the appropriate reports directory.

    Returns:
        Path: The Path object pointing to the reports directory.
    """
    if Path("reports").is_dir():
        return Path("reports")
    if Path("notebooks/reports").is_dir():
        return Path("notebooks/reports")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def _rank_from_cc(avg_cc: float) -> str:
    """Returns letter rank grade corresponding to cyclomatic complexity.

    Args:
        avg_cc: Average cyclomatic complexity score.

    Returns:
        Letter rank from 'A' (simplest) to 'F' (most complex).
    """
    if avg_cc <= 5:
        return "A"
    if avg_cc <= 10:
        return "B"
    if avg_cc <= 20:
        return "C"
    if avg_cc <= 30:
        return "D"
    if avg_cc <= 40:
        return "E"
    return "F"


def _score_from_cc(avg_cc: float) -> float:
    """Maps cyclomatic complexity to a 0.0 - 100.0 percentage quality score.

    Args:
        avg_cc: Average cyclomatic complexity score.

    Returns:
        Percentage score where low complexity receives high score.
    """
    # CC 1-5 (Rank A) -> 90-100%
    # CC 6-10 (Rank B) -> 75-89%
    # CC 11-20 (Rank C) -> 60-74%
    # CC 21-30 (Rank D) -> 40-59%
    # CC 31-40 (Rank E) -> 20-39%
    # CC > 40 (Rank F) -> 0-19%
    if avg_cc <= 1.0:
        return 100.0
    if avg_cc <= 5.0:
        return max(90.0, 100.0 - (avg_cc - 1.0) * 2.5)
    if avg_cc <= 10.0:
        return max(75.0, 90.0 - (avg_cc - 5.0) * 3.0)
    if avg_cc <= 20.0:
        return max(60.0, 75.0 - (avg_cc - 10.0) * 1.5)
    if avg_cc <= 30.0:
        return max(40.0, 60.0 - (avg_cc - 20.0) * 2.0)
    if avg_cc <= 40.0:
        return max(20.0, 40.0 - (avg_cc - 30.0) * 2.0)
    return max(0.0, 20.0 - (avg_cc - 40.0) * 0.5)


async def get_complexity_score(
    file_path: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """Runs Radon on a Python file or directory and returns complexity metrics.

    Args:
        file_path: The path to the Python file or directory to analyze.
        path: Optional alias for file_path for backwards compatibility.

    Returns:
        A dictionary containing maintainability index, average cyclomatic
        complexity, corresponding ranks, composite complexity score, and report file path.
    """
    target_path = file_path if file_path is not None else path
    if not target_path:
        return {"error": "Error: No file or directory path provided."}

    if not os.path.exists(target_path):
        return {"error": f"Error: Target path not found at {target_path}"}

    is_dir = os.path.isdir(target_path)
    if not is_dir and not target_path.endswith(".py"):
        return {"error": "Error: Not a Python file."}

    try:
        absolute_target_path = os.path.abspath(target_path)
        radon_bin = shutil.which("radon") or "radon"

        # 1. Run Maintainability Index (MI) with JSON output
        mi_proc = await asyncio.create_subprocess_exec(
            radon_bin, "mi", "-s", "-j", absolute_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            mi_stdout, mi_stderr = await asyncio.wait_for(
                mi_proc.communicate(), timeout=RADON_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            mi_proc.kill()
            return {"error": f"Radon MI timed out after {RADON_TIMEOUT_SECONDS} seconds."}

        # 2. Run Cyclomatic Complexity (CC) with JSON output
        cc_proc = await asyncio.create_subprocess_exec(
            radon_bin, "cc", "-s", "-a", "-j", absolute_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            cc_stdout, cc_stderr = await asyncio.wait_for(
                cc_proc.communicate(), timeout=RADON_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            cc_proc.kill()
            return {"error": f"Radon CC timed out after {RADON_TIMEOUT_SECONDS} seconds."}

        # 3. Generate human-readable text report
        txt_proc = await asyncio.create_subprocess_exec(
            radon_bin, "cc", "-s", "-a", absolute_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        txt_out_cc, _ = await asyncio.wait_for(
            txt_proc.communicate(), timeout=RADON_TIMEOUT_SECONDS
        )

        txt_mi_proc = await asyncio.create_subprocess_exec(
            radon_bin, "mi", "-s", absolute_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        txt_out_mi, _ = await asyncio.wait_for(
            txt_mi_proc.communicate(), timeout=RADON_TIMEOUT_SECONDS
        )

        # Save combined human-readable report
        reports_dir = _get_reports_dir()
        report_file_path = reports_dir / "radon_report.txt"
        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Radon Cyclomatic Complexity for {target_path} ---\n")
            f.write(txt_out_cc.decode("utf-8", errors="replace"))
            f.write(f"\n--- Radon Maintainability Index for {target_path} ---\n")
            f.write(txt_out_mi.decode("utf-8", errors="replace"))

        # Parse MI data
        mi_str = mi_stdout.decode("utf-8", errors="replace").strip()
        mi_data = json.loads(mi_str) if mi_str else {}

        # Parse CC data
        cc_str = cc_stdout.decode("utf-8", errors="replace").strip()
        cc_data = json.loads(cc_str) if cc_str else {}

        # Calculate average MI
        mi_values = []
        for file_info in mi_data.values():
            if isinstance(file_info, dict) and "mi" in file_info:
                mi_values.append(float(file_info["mi"]))

        avg_mi = sum(mi_values) / len(mi_values) if mi_values else 100.0
        avg_mi = max(0.0, min(100.0, avg_mi))
        mi_rank = "A" if avg_mi >= 20.0 else ("B" if avg_mi >= 10.0 else "C")

        # Calculate average CC across all functions and methods
        cc_complexities = []
        blocks_summary = []
        for file_k, block_list in cc_data.items():
            if isinstance(block_list, list):
                for b in block_list:
                    c = b.get("complexity", 1)
                    cc_complexities.append(c)
                    blocks_summary.append(
                        f"{b.get('name', 'block')} (line {b.get('lineno', '?')}): "
                        f"Rank {b.get('rank', 'A')} (Complexity: {c})"
                    )

        avg_cc = (
            sum(cc_complexities) / len(cc_complexities)
            if cc_complexities
            else 1.0
        )
        cc_rank = _rank_from_cc(avg_cc)
        cc_score = _score_from_cc(avg_cc)

        # Composite score weighting: 50% Maintainability Index, 50% Complexity Score
        composite_score = round(0.5 * avg_mi + 0.5 * cc_score, 2)

        return {
            "maintainability_index": round(avg_mi, 2),
            "maintainability_rank": mi_rank,
            "average_complexity": round(avg_cc, 2),
            "complexity_rank": cc_rank,
            "complexity_score": composite_score,
            "analyzed_blocks_count": len(cc_complexities),
            "blocks_summary": blocks_summary[:10],
            "report_file": str(report_file_path)
        }

    except Exception as e:
        return {"error": f"An unexpected error occurred during complexity analysis: {e}"}


# Alias for flexible importing
get_complexity_metrics = get_complexity_score
