# Python CLI Prettify with Rich

Beautifying Python CLIs using the Rich library.

## Overview

Rich is a Python library for rich text and beautiful formatting in the terminal. It integrates seamlessly with Typer for stunning CLI output.

## Console

```python
from rich.console import Console

console = Console()
console.print("[bold green]Success![/bold green]")
console.print("[red]Error:[/red] something went wrong")
```

## Tables

```python
from rich.table import Table

table = Table(title="Users", show_header=True, header_style="bold blue")
table.add_column("ID", style="dim", width=6)
table.add_column("Name", style="bold")
table.add_column("Email")

table.add_row("1", "Alice", "alice@example.com")
console.print(table)
```

## Panels

```python
from rich.panel import Panel

console.print(Panel("Hello, [bold magenta]World[/bold magenta]!", title="Greeting"))
```

## Progress

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

## Best Practices

1. Create a single shared `console` instance
2. Use markup tags `[bold]`, `[red]`, `[link]` for styling
3. Use `console.print` instead of `print`
4. Use `Panel` for section headers
5. Use `Table` for structured data
