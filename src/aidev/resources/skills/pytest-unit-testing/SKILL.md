# Pytest Unit Testing Skill

Writing effective unit tests with pytest in Python projects.

## Overview

pytest is the de facto standard for Python testing. This skill covers writing clean, maintainable, and reliable unit tests.

## Key Patterns

### Fixtures
Use `@pytest.fixture` for shared test setup and teardown:

```python
import pytest

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}

def test_user_name(sample_user):
    assert sample_user["name"] == "Alice"
```

### Parametrize
Use `@pytest.mark.parametrize` for data-driven tests:

```python
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

### Mocking
Use `pytest-mock` or `unittest.mock`:

```python
def test_service_calls_api(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {"status": "ok"}
    result = my_service.check_status()
    assert result == "ok"
    mock_get.assert_called_once()
```

### tmp_path Fixture
Use `tmp_path` for filesystem tests:

```python
def test_write_file(tmp_path):
    file = tmp_path / "output.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"
```

## Best Practices

1. **One assertion per test** - keep tests focused
2. **Descriptive names** - `test_user_creation_with_valid_email` not `test_user`
3. **Arrange-Act-Assert** - structure tests clearly
4. **Avoid testing implementation details** - test behavior
5. **Fast tests** - mock external dependencies
6. **Isolated tests** - no shared mutable state between tests
7. **Use conftest.py** - share fixtures across test files

## Running Tests

```bash
pytest tests/                    # run all tests
pytest tests/unit/ -v            # verbose unit tests
pytest -k "test_user"            # run matching tests
pytest --cov=src --cov-report=html  # with coverage
pytest -x                        # stop on first failure
```
