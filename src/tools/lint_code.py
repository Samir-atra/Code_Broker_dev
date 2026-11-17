"""Linting tool module for Python code quality assessment.

This module provides utility functions to run pylint on target Python files,
save the complete lint output to a report file, and parse the resulting score.
"""

import asyncio
import os
from pathlib import Path
import re
import shutil

PYLINT_TIMEOUT_SECONDS = 60


def _get_reports_dir() -> Path:
    """Finds or creates the appropriate reports directory.

    Returns:
        Path: The Path object pointing to the reports directory.
    """
    # If executed within notebooks/ directory
    if Path("reports").is_dir():
        return Path("reports")
    # If executed from repository root where notebooks/reports exists
    if Path("notebooks/reports").is_dir():
        return Path("notebooks/reports")
    # Default fallback: create reports directory in current working directory
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


async def get_linting_score(file_path: str = None, path: str = None) -> dict:
    """Runs pylint on a given Python file and returns its linting score.

    Args:
        file_path: The path to the Python file to lint.
        path: Optional alias for file_path for backwards compatibility.

    Returns:
        A dictionary containing the linting score as a float and any errors,
        or an error message if the file is not found or pylint fails.
    """
    target_path = file_path if file_path is not None else path
    if not target_path:
        return {"error": "Error: No file path provided."}

    if not os.path.exists(target_path):
        return {"error": f"Error: File not found at {target_path}"}
    if not target_path.endswith('.py'):
        return {"error": "Error: Not a Python file."}

    try:
        # Resolve absolute file path and locate pylint binary
        absolute_file_path = os.path.abspath(target_path)
        pylint_bin = shutil.which("pylint") or "pylint"

        # Execute Pylint directly so timeout handling applies to the analyzer process.
        try:
            process = await asyncio.create_subprocess_exec(
                pylint_bin,
                absolute_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except (FileNotFoundError, OSError) as e:
            return {"error": f"Unable to start Pylint: {e}"}

        timed_out = False
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=PYLINT_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            timed_out = True

        pylint_output = stdout.decode()
        pylint_error = stderr.decode()

        # Save pylint output to a file in the reports directory
        reports_dir = _get_reports_dir()
        report_file_path = reports_dir / "pylint_report.txt"
        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Pylint Output for {target_path} ---\n{pylint_output}")
            if pylint_error:
                f.write(f"\n--- Pylint Errors for {target_path} ---\n{pylint_error}\n")

        if timed_out:
            return {
                "error": f"Pylint timed out after {PYLINT_TIMEOUT_SECONDS} seconds.",
                "pylint_output": pylint_output,
                "pylint_error": pylint_error
            }

        pylint_exit_code = process.returncode
        if pylint_exit_code is None:
            return {"error": "Pylint exited without a return code."}

        # Pylint's nonzero status also encodes ordinary findings; 1 and 32
        # specifically represent fatal and usage errors.
        if pylint_exit_code & (1 | 32):
            return {
                "error": f"Pylint failed with exit code {pylint_exit_code}.",
                "pylint_exit_code": pylint_exit_code,
                "pylint_output": pylint_output,
                "pylint_error": pylint_error
            }

        # Extract the score using a regular expression
        match = re.search(r"Your code has been rated at ([-+]?\d*\.\d+|\d+)/10", pylint_output)
        if match:
            score_out_of_10 = float(match.group(1))
            percentage_score = score_out_of_10 * 10  # Convert to percentage
            return {
                "linting_score": percentage_score,
                "pylint_exit_code": pylint_exit_code
            }
        else:
            return {
                "error": "Pylint completed but no score could be extracted.",
                "pylint_exit_code": pylint_exit_code,
                "pylint_output": pylint_output,
                "pylint_error": pylint_error
            }

    except Exception as e:
        return {"error": f"An unexpected error occurred during linting: {e}"}
    