"""Security scanning tool module for Python code quality assessment.

This module provides utility functions to run Bandit static security analysis
on target Python files or directories, save the complete scan output to a
report file, and compute a calibrated security quality score.
"""

import asyncio
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

BANDIT_TIMEOUT_SECONDS = 60


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


async def get_security_score(
    file_path: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """Runs Bandit on a Python file or directory and returns security metrics.

    Args:
        file_path: The path to the Python file or directory to scan.
        path: Optional alias for file_path for backwards compatibility.

    Returns:
        A dictionary containing the security score (0.0 to 100.0), issue counts
        by severity, structured findings summary, report file path, and any errors.
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
        bandit_bin = shutil.which("bandit") or "bandit"

        # Build command args for JSON machine-readable output
        json_cmd = [bandit_bin, "-f", "json"]
        if is_dir:
            json_cmd.append("-r")
        json_cmd.append(absolute_target_path)

        # Execute JSON scan
        try:
            process = await asyncio.create_subprocess_exec(
                *json_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except (FileNotFoundError, OSError) as e:
            return {"error": f"Unable to start Bandit: {e}"}

        timed_out = False
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=BANDIT_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            timed_out = True

        raw_output = stdout.decode("utf-8", errors="replace")
        raw_error = stderr.decode("utf-8", errors="replace")

        if timed_out:
            return {
                "error": f"Bandit timed out after {BANDIT_TIMEOUT_SECONDS} seconds.",
                "bandit_output": raw_output,
                "bandit_error": raw_error
            }

        # Also generate human-readable text report for archiving
        txt_cmd = [bandit_bin, "-f", "txt"]
        if is_dir:
            txt_cmd.append("-r")
        txt_cmd.append(absolute_target_path)

        try:
            txt_proc = await asyncio.create_subprocess_exec(
                *txt_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            txt_out, txt_err = await asyncio.wait_for(
                txt_proc.communicate(), timeout=BANDIT_TIMEOUT_SECONDS
            )
            human_report = txt_out.decode("utf-8", errors="replace")
            if txt_err:
                human_report += "\n--- Warnings/Errors ---\n" + txt_err.decode(
                    "utf-8", errors="replace"
                )
        except Exception:
            human_report = raw_output

        # Save report to reports directory
        reports_dir = _get_reports_dir()
        report_file_path = reports_dir / "bandit_report.txt"
        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Bandit Security Report for {target_path} ---\n{human_report}\n")

        # Parse JSON output
        # Bandit may exit with returncode 1 when issues are found, which is normal
        json_str = raw_output.strip()
        # Locate the JSON object boundary if log messages are prepended/appended
        brace_start = json_str.find("{")
        brace_end = json_str.rfind("}")
        if brace_start != -1 and brace_end != -1:
            json_str = json_str[brace_start:brace_end + 1]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse Bandit JSON output: {e}",
                "bandit_output": raw_output,
                "bandit_error": raw_error,
            }

        results: List[Dict[str, Any]] = data.get("results", [])
        totals = data.get("metrics", {}).get("_totals", {})

        high_count = totals.get("SEVERITY.HIGH", 0)
        medium_count = totals.get("SEVERITY.MEDIUM", 0)
        low_count = totals.get("SEVERITY.LOW", 0)
        total_issues = len(results)

        # Compute calibrated security score out of 100.0:
        # Penalties: High = 25 pts, Medium = 12 pts, Low = 5 pts
        penalty = (high_count * 25.0) + (medium_count * 12.0) + (low_count * 5.0)
        security_score = max(0.0, min(100.0, 100.0 - penalty))

        # Summarize key findings for agent consumption
        findings = []
        for r in results[:10]:  # Cap top 10 findings for concise LLM context
            test_id = r.get("test_id", "Unknown")
            issue_text = r.get("issue_text", "")
            severity = r.get("issue_severity", "UNKNOWN")
            confidence = r.get("issue_confidence", "UNKNOWN")
            line_num = r.get("line_number", 0)
            file_name = Path(r.get("filename", "")).name
            findings.append(
                f"[{test_id}] {issue_text} ({file_name}:{line_num}) - "
                f"Severity: {severity}, Confidence: {confidence}"
            )

        return {
            "security_score": round(security_score, 2),
            "total_issues": total_issues,
            "severity_counts": {
                "HIGH": high_count,
                "MEDIUM": medium_count,
                "LOW": low_count
            },
            "findings_summary": findings,
            "report_file": str(report_file_path)
        }

    except Exception as e:
        return {"error": f"An unexpected error occurred during security scan: {e}"}
