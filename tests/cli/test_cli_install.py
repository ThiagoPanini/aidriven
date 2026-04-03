import pytest
from pathlib import Path
from typer.testing import CliRunner
from aidev.cli import app

runner = CliRunner()


def test_install_resource(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "pytest-unit-testing"])
    assert result.exit_code == 0
    assert "pytest-unit-testing" in result.output or "Installed" in result.output


def test_install_type_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "--type", "skill"])
    assert result.exit_code == 0


def test_install_nonexistent_resource(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "nonexistent-resource-xyz"])
    assert result.exit_code != 0


def test_install_with_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install", "pytest-unit-testing"])
    result = runner.invoke(app, ["install", "--force", "pytest-unit-testing"])
    assert result.exit_code == 0


def test_install_no_args_shows_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install"])
    assert result.exit_code != 0
