---
name: python-unit-tests
description: >
  Generate high-quality Python unit tests using pytest, organized with the Given/When/Then (GWT)
  pattern. Invoke this skill whenever a user wants to create, generate, write, or add Python tests
  for any code — functions, classes, services, APIs, or modules. Trigger on requests like "write
  tests for this", "generate unit tests", "add test coverage", "create pytest tests", "test this
  function", "I need tests for my Python code", "write GWT tests", or "help me test this class".
  Also use this skill when the user pastes Python code and asks for tests, asks how to test
  something, wants to improve existing test coverage, or needs tests for edge cases, error handling,
  or validation logic. Even if the user doesn't say "GWT" or "Given/When/Then", use this skill
  for any Python test generation request.
---

# Python Unit Test Generator

Generate production-ready Python unit tests using pytest with the Given/When/Then (GWT) pattern.
The tests produced by this skill prioritize observable behavior over implementation details,
follow professional software engineering standards, and are ready to run without modification.

## Why GWT Matters

The Given/When/Then pattern makes tests self-documenting. Anyone reading the test immediately
understands what scenario is set up (Given), what action is performed (When), and what outcome
is expected (Then). This structure prevents the common failure mode where tests exist but nobody
understands what they actually verify. Every test method produced by this skill uses GWT both in
its docstring and in its code structure.

---

## Phase 1 — Analyze the Input Code

Before writing any tests, read and understand the code under test:

1. **Identify the unit** — What is being tested? A function, a class, a module?
2. **Map the public interface** — List every public method/function, its parameters, return types,
   and side effects. Focus on the public API — tests should exercise what the code promises, not
   how it's internally wired.
3. **Identify dependencies** — Does the code call external services, databases, file systems,
   or other modules? These will need mocking.
4. **Spot the edge cases** — What happens with empty inputs, None values, boundary values,
   invalid types, large inputs, concurrent access?
5. **Check for exceptions** — Which exceptions can the code raise, and under what conditions?
6. **Note parameterizable scenarios** — Where does the same logic apply across multiple inputs
   with different expected outputs?

If the input code has ambiguities (e.g., unclear return type, undocumented side effects), state
your assumptions explicitly in a comment at the top of the test file rather than guessing silently.

---

## Phase 2 — Plan Test Coverage

Organize tests into logical groups. Each group becomes a test class. The grouping should reflect
the structure of the code under test:

| Code Structure | Test Organization |
|---|---|
| Single function | One class per function, methods cover scenarios |
| Class with methods | One test class per method or per logical feature |
| Module with related functions | One test class per function or per feature group |
| Service with dependencies | One test class per operation, with shared fixtures |

For each unit, plan test cases across these categories:

- **Happy path** — Normal inputs producing expected outputs
- **Edge cases** — Boundary values, empty collections, zero, None, single-element lists
- **Error cases** — Invalid inputs, missing dependencies, exception scenarios
- **Parameterized cases** — Same logic, multiple input/output pairs

---

## Phase 3 — Generate Tests

### File Structure

```python
"""Tests for <module_under_test>.

Assumptions (if any):
- <assumption about unclear behavior>
"""

from __future__ import annotations

import pytest
# Import mocking tools only when needed
# from unittest.mock import MagicMock, Mock, patch, PropertyMock

from <module> import <unit_under_test>


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def <fixture_name>():
    """<What this fixture provides>."""
    ...


# ── <UnitUnderTest> ───────────────────────────────────────────────────

class TestUnitUnderTest:
    """Tests for <unit_under_test>."""

    def test_<scenario_in_snake_case>(self):
        """
        Given <precondition>,
        When <action>,
        Then <expected outcome>.
        """
        # ── Given ──
        ...

        # ── When ──
        result = ...

        # ── Then ──
        assert ...
```

### Test Method Rules

1. **Name**: `test_<what_it_verifies>` in snake_case. The name should describe the scenario,
   not restate the implementation. Good: `test_returns_empty_list_when_no_items_match`.
   Bad: `test_filter_1`, `test_it_works`.

2. **Docstring**: Every test method has a one-line or multi-line docstring in GWT format:
   ```python
   """
   Given a user with admin privileges,
   When they request the settings page,
   Then they receive a 200 response with admin controls.
   """
   ```

3. **Body structure**: Use `# ── Given ──`, `# ── When ──`, `# ── Then ──` comment separators
   to visually divide the three phases. This makes the structure scannable even without reading
   the docstring.

4. **One behavior per test**: Each test verifies exactly one behavior. If you find yourself
   writing multiple unrelated assertions, split into separate tests. Multiple assertions about
   the same result are fine (e.g., checking both the status code and the response body).

5. **No logic in tests**: Tests should not contain conditionals, loops, or complex computation.
   If the test needs a computed expected value, extract it into a helper or a fixture.

### Mocking Strategy

Mock at the boundary of the unit under test, not deep inside:

- **Do mock**: External services, I/O, system calls, time, randomness, third-party APIs
- **Don't mock**: The unit under test itself, pure helper functions it calls, data structures
- **Prefer `unittest.mock`**: Use `patch`, `MagicMock`, and `Mock` from the standard library.
  Reserve third-party mocking libraries for cases where `unittest.mock` is genuinely insufficient.
- **Patch target**: Always patch where the object is *used*, not where it's *defined*.
  ```python
  # Code under test: myapp/service.py imports requests
  # Correct:
  @patch("myapp.service.requests.get")
  # Wrong:
  @patch("requests.get")
  ```

### Fixtures

- Use `@pytest.fixture` for reusable setup that multiple tests share.
- Keep fixtures close to the tests that use them — define in the test file, not in a distant
  `conftest.py`, unless multiple test files genuinely share them.
- Name fixtures after what they provide, not how they create it. Good: `admin_user`.
  Bad: `create_user_and_set_admin_flag`.
- Use factory fixtures when tests need variations:
  ```python
  @pytest.fixture
  def make_user():
      def _make(name="Alice", role="viewer"):
          return User(name=name, role=role)
      return _make
  ```

### Parameterized Tests

Use `@pytest.mark.parametrize` when the same test logic applies to multiple inputs:

```python
class TestCalculateDiscount:
    """Tests for calculate_discount()."""

    @pytest.mark.parametrize(
        ("amount", "tier", "expected"),
        [
            (100.0, "bronze", 5.0),
            (100.0, "silver", 10.0),
            (100.0, "gold", 20.0),
            (0.0, "gold", 0.0),
        ],
        ids=["bronze-5%", "silver-10%", "gold-20%", "zero-amount"],
    )
    def test_applies_correct_discount_by_tier(self, amount, tier, expected):
        """
        Given an order amount and a membership tier,
        When the discount is calculated,
        Then the correct percentage is applied.
        """
        # ── Given ──
        # (parameters provide the given context)

        # ── When ──
        result = calculate_discount(amount, tier)

        # ── Then ──
        assert result == expected
```

Use `ids` to give each parameter set a human-readable name in test output.

### Exception Testing

```python
def test_raises_value_error_for_negative_amount(self):
    """
    Given a negative order amount,
    When the discount is calculated,
    Then a ValueError is raised with a descriptive message.
    """
    # ── Given ──
    amount = -50.0

    # ── When / Then ──
    with pytest.raises(ValueError, match="amount must be non-negative"):
        calculate_discount(amount, "gold")
```

When the exception is raised by the action itself, combine the When and Then phases with a
`# ── When / Then ──` comment to keep the code natural.

### Testing Classes with Dependencies

```python
class TestOrderService:
    """Tests for OrderService."""

    @pytest.fixture
    def mock_repo(self):
        """An in-memory mock of OrderRepository."""
        return MagicMock(spec=OrderRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """OrderService wired with mock dependencies."""
        return OrderService(repository=mock_repo)

    def test_creates_order_and_persists(self, service, mock_repo):
        """
        Given valid order data,
        When the order is created,
        Then the order is saved to the repository.
        """
        # ── Given ──
        order_data = {"item": "widget", "qty": 3}

        # ── When ──
        service.create_order(order_data)

        # ── Then ──
        mock_repo.save.assert_called_once()
        saved_order = mock_repo.save.call_args[0][0]
        assert saved_order.item == "widget"
        assert saved_order.qty == 3
```

---

## Phase 4 — Quality Checks

Before delivering the tests, verify against this checklist:

| Check | What to verify |
|---|---|
| **Runs clean** | Tests pass when the code under test is correct |
| **Fails correctly** | Tests fail when the code under test has a bug |
| **Isolated** | Each test can run independently, in any order |
| **Deterministic** | No random values, no time-dependent assertions, no flakiness |
| **No implementation coupling** | Refactoring internals without changing behavior should not break tests |
| **Complete coverage** | Happy path + edge cases + error cases are covered |
| **Readable** | A new developer can understand each test in under 30 seconds |
| **GWT structure** | Every test has GWT docstring and GWT comment separators |
| **Proper mocking** | Mocks are at boundaries, not deep inside the unit |
| **Descriptive names** | Test names describe scenarios, not implementation steps |

---

## Phase 5 — Deliver

Present the complete test file. If the test file is large, organize with section separators
between test classes:

```python
# ── TestCreateOrder ───────────────────────────────────────────────────

class TestCreateOrder:
    ...


# ── TestCancelOrder ───────────────────────────────────────────────────

class TestCancelOrder:
    ...
```

If the input code was ambiguous, summarize the assumptions made and invite the user to correct
them. If there are obvious gaps in the code under test (e.g., missing validation that should
exist), mention them as suggestions but don't add tests for behavior that doesn't exist yet.

---

## Constraints

- **Framework**: Use `pytest` as the test framework. Use `unittest.mock` for mocking.
  Do not use `unittest.TestCase` as a base class — use plain classes with pytest.
- **No test logic**: Tests must not contain `if`, `for`, `while`, or `try/except` blocks.
  Exception: `pytest.raises` context managers are fine.
- **No fragile tests**: Do not assert on string representations, memory addresses, or
  internal state that could change without affecting behavior.
- **No over-mocking**: If more than half the test is mock setup, the design likely needs
  rethinking. Flag this to the user rather than producing a brittle test.
- **Minimal assumptions**: When the code's behavior is ambiguous, state assumptions
  explicitly rather than inventing behavior.
- **Standard library first**: Prefer `unittest.mock` over third-party mocking libraries
  unless the user explicitly requests otherwise.

---

## Complete Example

Given this input code:

```python
# auth.py
from __future__ import annotations
import hashlib
import secrets

class AuthService:
    def __init__(self, user_repo, token_store):
        self._users = user_repo
        self._tokens = token_store

    def authenticate(self, username: str, password: str) -> str:
        user = self._users.find_by_username(username)
        if user is None:
            raise ValueError("Unknown user")
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if hashed != user.password_hash:
            raise ValueError("Invalid password")
        token = secrets.token_urlsafe(32)
        self._tokens.store(user.id, token)
        return token
```

The skill produces:

```python
"""Tests for AuthService.authenticate().

Assumptions:
- user_repo.find_by_username returns an object with .password_hash and .id attributes, or None.
- token_store.store(user_id, token) persists the token without returning a value.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auth import AuthService


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_repo():
    """A mock user repository."""
    return MagicMock()


@pytest.fixture
def mock_token_store():
    """A mock token store."""
    return MagicMock()


@pytest.fixture
def service(mock_user_repo, mock_token_store):
    """AuthService wired with mock dependencies."""
    return AuthService(user_repo=mock_user_repo, token_store=mock_token_store)


@pytest.fixture
def valid_user():
    """A user with a known password hash."""
    import hashlib

    user = MagicMock()
    user.id = 42
    user.password_hash = hashlib.sha256(b"correct-password").hexdigest()
    return user


# ── TestAuthenticate ──────────────────────────────────────────────────

class TestAuthenticate:
    """Tests for AuthService.authenticate()."""

    def test_returns_token_on_valid_credentials(
        self, service, mock_user_repo, mock_token_store, valid_user,
    ):
        """
        Given a registered user with correct credentials,
        When authenticate is called,
        Then a token string is returned and stored.
        """
        # ── Given ──
        mock_user_repo.find_by_username.return_value = valid_user

        # ── When ──
        token = service.authenticate("alice", "correct-password")

        # ── Then ──
        assert isinstance(token, str)
        assert len(token) > 0
        mock_token_store.store.assert_called_once_with(42, token)

    def test_raises_for_unknown_username(self, service, mock_user_repo):
        """
        Given a username that does not exist,
        When authenticate is called,
        Then a ValueError is raised indicating unknown user.
        """
        # ── Given ──
        mock_user_repo.find_by_username.return_value = None

        # ── When / Then ──
        with pytest.raises(ValueError, match="Unknown user"):
            service.authenticate("nobody", "any-password")

    def test_raises_for_wrong_password(
        self, service, mock_user_repo, valid_user,
    ):
        """
        Given a registered user with an incorrect password,
        When authenticate is called,
        Then a ValueError is raised indicating invalid password.
        """
        # ── Given ──
        mock_user_repo.find_by_username.return_value = valid_user

        # ── When / Then ──
        with pytest.raises(ValueError, match="Invalid password"):
            service.authenticate("alice", "wrong-password")

    def test_each_call_generates_unique_token(
        self, service, mock_user_repo, valid_user,
    ):
        """
        Given a registered user,
        When authenticate is called twice,
        Then two different tokens are returned.
        """
        # ── Given ──
        mock_user_repo.find_by_username.return_value = valid_user

        # ── When ──
        token_a = service.authenticate("alice", "correct-password")
        token_b = service.authenticate("alice", "correct-password")

        # ── Then ──
        assert token_a != token_b
```
