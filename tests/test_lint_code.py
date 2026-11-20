"""Tests for the Pylint subprocess wrapper."""

import asyncio

from src.tools import lint_code


class FakeProcess:
    def __init__(self, returncode, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.killed = False

    async def communicate(self):
        return self.stdout, self.stderr

    def kill(self):
        self.killed = True
        self.returncode = -9


def test_nonzero_lint_findings_still_return_score(monkeypatch, tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    process = FakeProcess(2, b"Your code has been rated at 7.50/10\n")

    async def start_process(*args, **kwargs):
        return process

    monkeypatch.setattr(lint_code.asyncio, "create_subprocess_exec", start_process)
    monkeypatch.setattr(lint_code, "_get_reports_dir", lambda: report_dir)

    result = asyncio.run(lint_code.get_linting_score(str(source)))

    assert result == {"linting_score": 75.0, "pylint_exit_code": 2}


def test_fatal_pylint_exit_code_returns_error(monkeypatch, tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    process = FakeProcess(1, b"Your code has been rated at 7.50/10\n")

    async def start_process(*args, **kwargs):
        return process

    monkeypatch.setattr(lint_code.asyncio, "create_subprocess_exec", start_process)
    monkeypatch.setattr(lint_code, "_get_reports_dir", lambda: report_dir)

    result = asyncio.run(lint_code.get_linting_score(str(source)))

    assert result["error"] == "Pylint failed with exit code 1."
    assert result["pylint_exit_code"] == 1


def test_pylint_timeout_kills_process_and_returns_error(monkeypatch, tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    process = FakeProcess(0)
    original_communicate = process.communicate

    async def slow_communicate():
        if not process.killed:
            await asyncio.sleep(0.1)
        return await original_communicate()

    process.communicate = slow_communicate

    async def start_process(*args, **kwargs):
        return process

    monkeypatch.setattr(lint_code.asyncio, "create_subprocess_exec", start_process)
    monkeypatch.setattr(lint_code, "_get_reports_dir", lambda: report_dir)
    monkeypatch.setattr(lint_code, "PYLINT_TIMEOUT_SECONDS", 0.01)

    result = asyncio.run(lint_code.get_linting_score(str(source)))

    assert result["error"] == "Pylint timed out after 0.01 seconds."
    assert process.killed
