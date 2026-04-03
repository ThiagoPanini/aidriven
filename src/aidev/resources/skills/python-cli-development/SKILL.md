# Python CLI Development with Typer

Building modern, type-safe command-line interfaces with Typer.

## Overview

Typer builds on top of Python type hints to create CLIs with minimal boilerplate. It generates help text, argument parsing, and shell completion automatically.

## App Setup

```python
import typer

app = typer.Typer(
    name="myapp",
    help="My awesome CLI tool",
    rich_markup_mode="rich",
)

if __name__ == "__main__":
    app()
```

## Commands

```python
@app.command()
def greet(name: str, count: int = 1) -> None:
    """Greet someone."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")
```

## Options and Arguments

```python
from typing import Optional
import typer

@app.command()
def deploy(
    environment: str = typer.Argument(..., help="Target environment"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Don't actually deploy"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t"),
) -> None:
    """Deploy to an environment."""
    ...
```

## Testing

```python
from typer.testing import CliRunner

runner = CliRunner()

def test_greet():
    result = runner.invoke(app, ["greet", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output
```

## Best Practices

1. Keep CLI layer thin - delegate to service functions
2. Use `Optional[str]` (not `str | None`) for Typer compatibility
3. Always provide help strings for commands, options, and arguments
4. Use `rich_markup_mode="rich"` for colored help text
5. Return proper exit codes (0=success, 1=error)
