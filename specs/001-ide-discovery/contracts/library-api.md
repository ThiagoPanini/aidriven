# Library API Contract: IDE Discovery Service

**Feature**: IDE Discovery Service
**Date**: 2026-04-05
**Type**: Internal Python library API

## Public API Surface

The discovery service exposes its public API exclusively through `aidriven.discovery`. All internal modules (`_models`, `_providers`, `_orchestrator`, `_platform`) are private implementation details.

### Entry Point

```python
from aidriven.discovery import discover_ides

result: DiscoveryResult = discover_ides()
```

**Signature**:
```python
def discover_ides(
    *,
    registry: ProviderRegistry | None = None,
) -> DiscoveryResult: ...
```

**Parameters**:
- `registry` (optional): A custom `ProviderRegistry` instance. When `None`, uses the default registry containing all built-in providers (VS Code, Cursor, Kiro). This parameter enables testing with mock providers and supports the extensibility requirement (FR-009).

**Returns**: `DiscoveryResult` — always returns, never raises. Provider failures are captured in `diagnostics`.

**Behavior**:
1. If `registry` is `None`, use the default global registry with built-in providers
2. Iterate over all registered providers
3. Call `provider.detect()` for each, catching any `Exception`
4. Aggregate all `DetectedIDE` results into a single list
5. Capture any provider exceptions as `ProviderDiagnostic` entries
6. Return `DiscoveryResult` with both lists

---

### Public Re-exports from `aidriven.discovery`

| Symbol | Type | Description |
|--------|------|-------------|
| `discover_ides` | `function` | Main entry point |
| `DiscoveryResult` | `dataclass` | Aggregate discovery output |
| `DetectedIDE` | `dataclass` | Single detected IDE |
| `ConfidenceLevel` | `enum` | Detection confidence |
| `IDEProvider` | `Protocol` | Provider contract |
| `ProviderRegistry` | `class` | Provider registration |
| `ProviderDiagnostic` | `dataclass` | Diagnostic entry |
| `calculate_confidence` | `function` | Confidence level calculation |

### `__all__` Declaration

```python
__all__ = [
    "discover_ides",
    "DiscoveryResult",
    "DetectedIDE",
    "ConfidenceLevel",
    "IDEProvider",
    "ProviderRegistry",
    "ProviderDiagnostic",
    "calculate_confidence",
]
```

---

## Usage Patterns

### Basic Discovery

```python
from aidriven.discovery import discover_ides

result = discover_ides()

for ide in result.detected_ides:
    print(f"{ide.display_name} ({ide.channel}) at {ide.install_path}")
    print(f"  Version: {ide.version or 'unknown'}")
    print(f"  Confidence: {ide.confidence.value}")

if result.diagnostics:
    for diag in result.diagnostics:
        print(f"Warning: {diag.provider_name} failed: {diag.message}")
```

### Filtering by IDE

```python
result = discover_ides()
vscode_installs = result.by_identifier("vscode")
viable = result.viable_ides
```

### Custom Provider Registration

```python
from aidriven.discovery import (
    IDEProvider,
    ProviderRegistry,
    DetectedIDE,
    discover_ides,
)

class WindsurfProvider:
    @property
    def name(self) -> str:
        return "Windsurf"

    def detect(self) -> list[DetectedIDE]:
        # ... detection logic ...
        return []

registry = ProviderRegistry()
registry.register(WindsurfProvider())
result = discover_ides(registry=registry)
```

---

## Error Handling Contract

| Scenario | Behavior | Spec Ref |
|----------|----------|----------|
| No IDEs installed | Returns `DiscoveryResult` with empty `detected_ides`, empty `diagnostics` | US-1 AC-3 |
| Provider raises exception | Exception caught; other providers continue; error in `diagnostics` | FR-010, SC-005 |
| Unsupported platform | Provider returns empty list (no paths to check); logged at DEBUG | Edge case |
| Permission denied on path | Path skipped; confidence reduced if partial evidence found | Edge case, US-3 |
| CLI tool hangs | `subprocess.run()` timeout (5s); treated as version-unavailable | RT-05 |

## Non-Functional Guarantees

- **No side effects**: `discover_ides()` performs read-only filesystem inspection (FR-014)
- **No network I/O**: Zero network calls under any circumstances (FR-014, G18)
- **Deterministic**: Same filesystem state produces same result
- **Performance**: < 2 seconds for full scan (SC-002)
