"""BugsInPy and test execution assessment tool module.

This module provides utility functions to evaluate test coverage, run
BugsInPy benchmark tests and pytest/unittest suites on target code,
output comprehensive test execution reports, and compute quantitative
test reliability scores.
"""

import asyncio
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional

BUGSINPY_TIMEOUT_SECONDS = 60
DEFAULT_BUGSINPY_DIR = Path("/home/samer/bugsinpy/framework/bin")


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


def _find_bugsinpy_bin(binary_name: str = "bugsinpy-test") -> Optional[str]:
    """Locates a BugsInPy framework executable.

    Args:
        binary_name: Name of the binary to locate.

    Returns:
        Path string to binary if found, else None.
    """
    found = shutil.which(binary_name)
    if found:
        return found
    candidate = DEFAULT_BUGSINPY_DIR / binary_name
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


async def get_test_score(
    file_path: Optional[str] = None,
    path: Optional[str] = None,
    project_name: Optional[str] = None,
    bug_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Evaluates test coverage and executes test suites on target code.

    Supports BugsInPy benchmark projects (via bugsinpy-test/bugsinpy-info) as well
    as native pytest/unittest test suites in arbitrary Python codebases.

    Args:
        file_path: Path to the target Python file or directory.
        path: Optional alias for file_path.
        project_name: Optional BugsInPy benchmark project name (e.g. 'youtube-dl').
        bug_id: Optional BugsInPy bug index.

    Returns:
        Dictionary with test score (0.0 to 100.0%), test counts, pass rate,
        framework used, and report file location.
    """
    target_path = file_path if file_path is not None else path
    reports_dir = _get_reports_dir()
    report_file_path = reports_dir / "bugsinpy_test_report.txt"

    # Case 1: Explicit BugsInPy project benchmark assessment
    if project_name:
        bip_test_bin = _find_bugsinpy_bin("bugsinpy-test")
        bip_info_bin = _find_bugsinpy_bin("bugsinpy-info")
        if not bip_test_bin:
            return {
                "error": "BugsInPy framework executable (bugsinpy-test) not found.",
                "test_score": 0.0,
                "has_tests": False,
            }

        cmd = [bip_test_bin]
        if target_path and os.path.isdir(target_path):
            cmd.extend(["-w", os.path.abspath(target_path)])
        if bug_id:
            cmd.append("-r")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=BUGSINPY_TIMEOUT_SECONDS
            )
            raw_out = stdout.decode("utf-8", errors="replace")
            raw_err = stderr.decode("utf-8", errors="replace")

            # Check bugsinpy-info if available
            info_text = ""
            if bip_info_bin and project_name:
                try:
                    info_args = [bip_info_bin, "-p", project_name]
                    if bug_id:
                        info_args.extend(["-i", str(bug_id)])
                    info_proc = await asyncio.create_subprocess_exec(
                        *info_args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    info_out, _ = await asyncio.wait_for(
                        info_proc.communicate(), timeout=15
                    )
                    info_text = info_out.decode("utf-8", errors="replace")
                except Exception:
                    pass

            passed = proc.returncode == 0
            test_score = 100.0 if passed else 0.0

            with open(report_file_path, "w", encoding="utf-8") as f:
                f.write(f"--- BugsInPy Test Report for Project: {project_name} ---\n")
                if info_text:
                    f.write(f"{info_text}\n\n")
                f.write(f"--- Test Execution Output ---\n{raw_out}\n")
                if raw_err:
                    f.write(f"--- Errors ---\n{raw_err}\n")

            return {
                "test_score": test_score,
                "has_tests": True,
                "tests_passed": 1 if passed else 0,
                "tests_failed": 0 if passed else 1,
                "framework_used": "BugsInPy",
                "project_name": project_name,
                "bug_id": bug_id,
                "report_file": str(report_file_path),
                "summary": f"BugsInPy test suite executed. Result: {'PASSED (100%)' if passed else 'FAILED (0%)'}",
            }
        except Exception as e:
            return {"error": f"BugsInPy execution failed: {e}", "test_score": 0.0}

    # Case 2: Codebase path assessment
    if not target_path:
        return {"error": "Error: No file or directory path provided."}

    if not os.path.exists(target_path):
        return {"error": f"Error: Target path not found at {target_path}"}

    target_obj = Path(target_path).resolve()

    # Determine test search directory
    if target_obj.is_file():
        # Check if file has a corresponding test file
        test_dir = target_obj.parent
        test_files = list(test_dir.glob("test_*.py")) + list(test_dir.glob("*_test.py"))
        # Check sibling tests/ directory
        sibling_tests = test_dir / "tests"
        if sibling_tests.is_dir():
            test_files.extend(list(sibling_tests.glob("test_*.py")))
        parent_tests = target_obj.parent.parent / "tests"
        if parent_tests.is_dir():
            # Check if this specific module is referenced
            test_files.extend(list(parent_tests.glob(f"test_{target_obj.stem}.py")))
            if not test_files:
                test_files.extend(list(parent_tests.glob("test_*.py")))
    else:
        test_files = list(target_obj.rglob("test_*.py")) + list(target_obj.rglob("*_test.py"))
        # Filter out virtual environments and git
        test_files = [
            f for f in test_files
            if not any(part in {".git", ".venv", "venv", "__pycache__"} for part in f.parts)
        ]

    # If no tests exist: score is 0.0% (as expected when test coverage is absent)
    if not test_files:
        summary_msg = f"No automated test files found for {target_path}. Test coverage is 0.0%."
        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- BugsInPy & Test Coverage Report for {target_path} ---\n")
            f.write(f"{summary_msg}\n")
            f.write("Recommendation: Author unit tests in a tests/ directory using pytest or unittest.\n")

        return {
            "test_score": 0.0,
            "has_tests": False,
            "tests_found": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework_used": "None",
            "report_file": str(report_file_path),
            "summary": summary_msg,
        }

    # Execute pytest or unittest on discovered tests
    pytest_bin = shutil.which("pytest") or "pytest"
    test_target = str(test_files[0].parent) if len(test_files) > 1 else str(test_files[0])

    try:
        proc = await asyncio.create_subprocess_exec(
            pytest_bin,
            "-q",
            "--tb=short",
            test_target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=BUGSINPY_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            return {
                "error": f"Test runner timed out after {BUGSINPY_TIMEOUT_SECONDS}s.",
                "test_score": 0.0,
                "has_tests": True
            }

        raw_out = stdout.decode("utf-8", errors="replace")
        raw_err = stderr.decode("utf-8", errors="replace")

        # Parse pytest output: e.g. "35 passed in 5.11s" or "2 failed, 33 passed"
        passed_match = re.search(r"(\d+)\s+passed", raw_out)
        failed_match = re.search(r"(\d+)\s+failed", raw_out)
        error_match = re.search(r"(\d+)\s+error", raw_out)

        passed_count = int(passed_match.group(1)) if passed_match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0
        error_count = int(error_match.group(1)) if error_match else 0
        total_tests = passed_count + failed_count + error_count

        if total_tests > 0:
            test_score = round((passed_count / total_tests) * 100.0, 2)
        else:
            test_score = 100.0 if proc.returncode == 0 else 0.0

        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Test Execution Report for {target_path} ---\n")
            f.write(f"Target: {test_target}\n")
            f.write(f"Discovered test files: {len(test_files)}\n")
            f.write(f"Passed: {passed_count}, Failed: {failed_count}, Errors: {error_count}\n")
            f.write(f"Calculated Test Score: {test_score}%\n\n")
            f.write(f"--- Raw Test Output ---\n{raw_out}\n")
            if raw_err:
                f.write(f"--- Stderr ---\n{raw_err}\n")

        return {
            "test_score": test_score,
            "has_tests": True,
            "test_files_count": len(test_files),
            "tests_passed": passed_count,
            "tests_failed": failed_count,
            "tests_errors": error_count,
            "framework_used": "pytest",
            "report_file": str(report_file_path),
            "summary": (
                f"{passed_count} passed, {failed_count} failed out of {total_tests} tests. "
                f"Test Score: {test_score}%"
            ),
        }

    except Exception as e:
        return {"error": f"Failed running tests: {e}", "test_score": 0.0, "has_tests": True}


# Aliases for flexible naming
run_bugsinpy_test = get_test_score
get_test_assessment_score = get_test_score
