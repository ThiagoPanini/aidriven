"""CLI entry point for aidev."""
from __future__ import annotations

from typing import Optional
import typer
from rich.console import Console

import aidev.app as app_layer
from aidev.presentation.console import error, info, success, warning
from aidev.presentation.renderers import (
    render_installed_summary,
    render_lockfile_status,
    render_resource_detail,
    render_resource_table,
)

console = Console()

cli_app = typer.Typer(
    name="aidev",
    help="🤖 AI development resources manager",
    rich_markup_mode="rich",
    no_args_is_help=False,
)


@cli_app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """🤖 AI development resources manager."""
    if ctx.invoked_subcommand is None:
        # Interactive mode
        from aidev.presentation.prompts import prompt_action

        action = prompt_action()
        action = action.strip().lower()
        if action == "list":
            _do_list(None, None)
        elif action == "init":
            _do_init()
        elif action == "doctor":
            _do_doctor()
        else:
            info(f"Run [bold]aidev {action} --help[/bold] for more info.")


@cli_app.command(name="list")
def list_resources_cmd(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by resource type"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search term"),
) -> None:
    """List available AI development resources."""
    _do_list(type, search)


def _do_list(type: Optional[str], search: Optional[str]) -> None:
    try:
        resources = app_layer.list_resources(resource_type=type, search=search)
        render_resource_table(resources)
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@cli_app.command()
def inspect(slug: str = typer.Argument(..., help="Resource slug to inspect")) -> None:
    """Inspect a resource and show its content."""
    try:
        resource, content = app_layer.inspect_resource(slug)
        render_resource_detail(resource, content)
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@cli_app.command()
def install(
    slugs: Optional[list[str]] = typer.Argument(None, help="Resource slugs to install"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Install all of a type"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
) -> None:
    """Install one or more AI development resources."""
    from pathlib import Path

    project_dir = Path.cwd()

    if type:
        try:
            results = app_layer.install_by_type(type, project_dir=project_dir, force=force)
            if results:
                render_installed_summary(results)
                success(f"Installed {len(results)} resource(s) of type '{type}'.")
            else:
                warning(f"No new resources installed for type '{type}'.")
        except ValueError as e:
            error(str(e))
            raise typer.Exit(1)
    elif slugs:
        errors: list[str] = []
        installed_list = []
        for slug in slugs:
            try:
                result = app_layer.install_resources([slug], project_dir=project_dir, force=force)
                installed_list.extend(result)
                success(f"Installed '{slug}'.")
            except (ValueError, FileExistsError) as e:
                errors.append(str(e))
                error(str(e))
        if installed_list:
            render_installed_summary(installed_list)
        if errors:
            raise typer.Exit(1)
    else:
        error("Specify slug(s) or use --type to install all of a type.")
        raise typer.Exit(1)


@cli_app.command()
def remove(slug: str = typer.Argument(..., help="Resource slug to remove")) -> None:
    """Remove an installed resource."""
    from pathlib import Path

    project_dir = Path.cwd()
    removed = app_layer.remove_resource(slug, project_dir=project_dir)
    if removed:
        success(f"Removed '{slug}'.")
    else:
        warning(f"'{slug}' is not installed.")


@cli_app.command()
def update(
    slug: Optional[str] = typer.Argument(None, help="Resource slug to update (omit for all)"),
) -> None:
    """Update installed resources."""
    from pathlib import Path

    project_dir = Path.cwd()
    try:
        results = app_layer.update_resource(slug=slug, project_dir=project_dir)
        if results:
            render_installed_summary(results)
            success(f"Updated {len(results)} resource(s).")
        else:
            warning("Nothing to update.")
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@cli_app.command()
def init() -> None:
    """Initialize .aidev/ structure in current directory."""
    _do_init()


def _do_init() -> None:
    from pathlib import Path

    project_dir = Path.cwd()
    aidev_dir = app_layer.init_project(project_dir)
    success(f"Initialized aidev project at {aidev_dir}")


@cli_app.command()
def doctor() -> None:
    """Check project health and installed resources."""
    _do_doctor()


def _do_doctor() -> None:
    from pathlib import Path

    project_dir = Path.cwd()
    result = app_layer.doctor(project_dir)
    if result["initialized"]:
        success(f"Project initialized at {result['project_dir']}")
        render_lockfile_status(result["lockfile"])
        render_installed_summary(result["lockfile"].installed_resources)
    else:
        warning(f"Project at {result['project_dir']} is not initialized. Run [bold]aidev init[/bold].")


# Expose as `app` for the entry point
app = cli_app
