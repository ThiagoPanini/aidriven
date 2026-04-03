# Testing Constitution

Standards for writing reliable, maintainable tests.

## Coverage Standards

- Minimum 80% line coverage for all modules
- 100% coverage for critical business logic (financial, security)
- Coverage is a floor, not a target - aim for meaningful tests

## Test Naming

Pattern: `test_<unit>_<scenario>_<expected_outcome>`

```python
def test_user_creation_with_valid_email_succeeds(): ...
def test_user_creation_with_invalid_email_raises_value_error(): ...
```

## Test Structure

Use Arrange-Act-Assert (AAA):

```python
def test_order_total_includes_tax():
    # Arrange
    order = Order(items=[Item(price=100)])
    tax_rate = 0.1

    # Act
    total = order.calculate_total(tax_rate=tax_rate)

    # Assert
    assert total == 110
```

## Mocking Guidelines

1. Mock at the boundary - mock external services, not internal logic
2. Verify mock calls when behavior matters
3. Use `pytest-mock` (`mocker` fixture)
4. Don't mock what you own - use real objects where possible

## Anti-Patterns

- **Testing implementation** instead of behavior
- **Shared mutable state** between tests
- **Flaky tests** that depend on time or order
- **Over-mocking** that makes tests meaningless

## CI Requirements

- All tests must pass before merge
- Test failures block deployment
- Run tests on every pull request
