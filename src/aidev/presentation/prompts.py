import typer
from aidev.domain.models import Resource


def prompt_select_resources(resources: list[Resource]) -> list[Resource]:
    """Interactive multi-select using typer.confirm for each resource."""
    selected: list[Resource] = []
    for resource in resources:
        if typer.confirm(f"Install '{resource.slug}' ({resource.resource_type.value})?", default=False):
            selected.append(resource)
    return selected


def prompt_action() -> str:
    """Prompt for a top-level action in interactive mode."""
    typer.echo("Available actions: list, install, remove, update, inspect, init, doctor")
    return typer.prompt("Action")
