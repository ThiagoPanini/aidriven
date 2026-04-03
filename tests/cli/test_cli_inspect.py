from typer.testing import CliRunner
from aidev.cli import app

runner = CliRunner()


def test_inspect_valid_slug():
    result = runner.invoke(app, ["inspect", "pytest-unit-testing"])
    assert result.exit_code == 0
    assert "pytest" in result.output.lower()


def test_inspect_shows_content():
    result = runner.invoke(app, ["inspect", "python-cli-development"])
    assert result.exit_code == 0
    assert "typer" in result.output.lower() or "cli" in result.output.lower()


def test_inspect_nonexistent_slug():
    result = runner.invoke(app, ["inspect", "nonexistent-resource-xyz"])
    assert result.exit_code != 0


def test_inspect_rule():
    result = runner.invoke(app, ["inspect", "clean-arch-principles"])
    assert result.exit_code == 0
    assert "arch" in result.output.lower() or "clean" in result.output.lower()


def test_inspect_spec():
    result = runner.invoke(app, ["inspect", "spec-kit"])
    assert result.exit_code == 0
