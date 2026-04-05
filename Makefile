.PHONY: lint format typecheck test check all

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run mypy src

test:
	uv run pytest

check:
	uv run pre-commit run --all-files

all: lint format typecheck test
