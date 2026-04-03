from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from aidev.domain.models import InstalledResource, LockFile, Resource
from aidev.presentation.console import console


def render_resource_table(resources: list[Resource]) -> None:
    if not resources:
        console.print("[dim]No resources found.[/dim]")
        return

    table = Table(title="Available Resources", show_header=True, header_style="bold cyan")
    table.add_column("Slug", style="bold", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Name")
    table.add_column("Description")

    for r in resources:
        table.add_row(r.slug, r.resource_type.value, r.name, r.description[:80])

    console.print(table)


def render_resource_detail(resource: Resource, content: str) -> None:
    meta = (
        f"[bold]Slug:[/bold] {resource.slug}\n"
        f"[bold]Type:[/bold] {resource.resource_type.value}\n"
        f"[bold]Name:[/bold] {resource.name}\n"
        f"[bold]Description:[/bold] {resource.description}\n"
        f"[bold]Tags:[/bold] {', '.join(resource.tags) or '-'}"
    )
    console.print(Panel(meta, title=f"[bold cyan]{resource.name}[/bold cyan]", expand=False))

    preview = content[:3000] + ("..." if len(content) > 3000 else "")
    console.print(Panel(preview, title="[bold]Content Preview[/bold]"))


def render_installed_summary(installed: list[InstalledResource]) -> None:
    if not installed:
        console.print("[dim]No resources installed.[/dim]")
        return

    table = Table(title="Installed Resources", show_header=True, header_style="bold green")
    table.add_column("Slug", style="bold")
    table.add_column("Type", style="magenta")
    table.add_column("Installed At")
    table.add_column("Target Path", style="dim")

    for r in installed:
        table.add_row(r.slug, r.resource_type.value, r.installed_at[:19], r.target_path)

    console.print(table)


def render_lockfile_status(lockfile: LockFile) -> None:
    count = len(lockfile.installed_resources)
    text = Text()
    text.append(f"Lockfile version: {lockfile.lockfile_version}\n", style="bold")
    text.append(f"Installed resources: {count}", style="green" if count > 0 else "dim")
    console.print(Panel(text, title="[bold]Project Status[/bold]", expand=False))
