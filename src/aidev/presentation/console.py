from rich.console import Console

console = Console()


def success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def warning(message: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def info(message: str) -> None:
    console.print(f"[bold blue]ℹ[/bold blue] {message}")
