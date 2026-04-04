# aidriven

> A python CLI tool that helps developers to get and install useful AI resources

## Installation

```bash
pip install aidriven
```

## Usage

```python
import aidriven
```

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src/

# Serve docs locally
uv run mkdocs serve
```

## Contributing

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality on every commit.

```bash
# Install pre-commit (one-time setup)
uv tool install pre-commit
pre-commit install

# Run all hooks manually against all files
pre-commit run --all-files
```

## License

MIT — see [LICENSE](LICENSE).
