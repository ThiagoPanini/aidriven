from typer.testing import CliRunner
from aidev.cli import app

runner = CliRunner()


def test_list_shows_resources():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    # Should contain some resource names from our catalog
    assert "pytest" in result.output.lower() or "skill" in result.output.lower() or "rule" in result.output.lower()


def test_list_type_skill():
    result = runner.invoke(app, ["list", "--type", "skill"])
    assert result.exit_code == 0
    assert "skill" in result.output.lower()


def test_list_type_rule():
    result = runner.invoke(app, ["list", "--type", "rule"])
    assert result.exit_code == 0
    assert "rule" in result.output.lower()


def test_list_search_python():
    result = runner.invoke(app, ["list", "--search", "python"])
    assert result.exit_code == 0
    assert "python" in result.output.lower()


def test_list_invalid_type():
    result = runner.invoke(app, ["list", "--type", "invalid_type_xyz"])
    assert result.exit_code != 0


def test_list_short_flags():
    result = runner.invoke(app, ["list", "-t", "skill", "-s", "python"])
    assert result.exit_code == 0
