# CLI Contract: `aidriven install`

**Date**: 2026-04-07
**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

This document defines the user-facing CLI surface for the `install` subcommand. It is the binding contract used by `tests/cli/install/` to verify Constitution gates G2–G7.

---

## Synopsis

```
aidriven install <artifact-type> <artifact-name> [options]
```

Verb-noun grammar (Constitution §II): `install` is the verb, `<artifact-type>` is the noun.

---

## Arguments

| Argument | Required | Values | Notes |
|----------|----------|--------|-------|
| `<artifact-type>` | yes | `skill` (v1) | Validated against the supported-types registry (FR-002). Unknown type → exit 2. |
| `<artifact-name>` | yes | `^[a-z][a-z0-9-]{0,63}$` | Locally validated (FR-003) before any network call. Invalid name → exit 2. |

---

## Options

| Flag | Repeatable | Default | Description |
|------|------------|---------|-------------|
| `--ai <target>` | yes | *(auto-detect if omitted)* | AI target identifier (`claude`, `copilot`). Multiple `--ai` flags install for multiple targets in one run (FR-004, US2). When provided, no auto-detection runs (FR-012). |
| `--scope project\|user` | no | `project` | Installation scope (FR-005). Project root is resolved by walking up to `.git`, falling back to cwd (FR-005a). |
| `--copy` | no | off | Use copy mode instead of symlink mode (FR-007a, FR-008b). |
| `--force` | no | off | Re-fetch bypassing the cache; overwrite foreign or modified content (FR-007, FR-027, FR-031). |
| `--dry-run` | no | off | Build and print the install plan without writing anything (G6). |
| `--json` | no | off | Emit a single JSON document on stdout instead of human text (G5). |
| `--quiet` | no | off | Suppress non-error output (Constitution §III). |
| `--verbose` | no | off | Increase diagnostic detail; logs at DEBUG level (Constitution §III). |
| `--yes` | no | off | Bypass interactive confirmation in non-interactive contexts (G4). |
| `--no-cache` | no | off | Equivalent to `--force` for fetch only; does not enable overwrite (Constitution §IX). |
| `--help, -h` | no | — | Print help and exit 0. |
| `--version` | no | — | Print version and exit 0. |

**Mutual exclusion / interaction rules**:
- `--quiet` and `--verbose` are mutually exclusive → exit 2.
- `--dry-run` overrides `--force` for *writes* (no writes occur), but the planner still resolves the SHA and the manifest.
- `--json` implies machine output; spinners and colors are suppressed regardless of TTY.

---

## Output

### Human (default)

Per target, on success:
```
✓ claude  installed code-reviewer at .agents/skills/code-reviewer (symlink: .claude/skills/code-reviewer)
✓ copilot installed code-reviewer at .agents/skills/code-reviewer (no symlink needed)
```

Idempotent re-run:
```
• claude  code-reviewer already up to date (sha256:abc123…)
```

Conflict (no `--force`):
```
✗ claude  refusing to overwrite .claude/skills/code-reviewer (modified or foreign content)
          re-run with --force to overwrite, or remove the directory first.
```

ANSI color and the `✓ ✗ •` glyphs are emitted only when stdout is a TTY and `NO_COLOR` is unset (G3).

### `--json`

A single JSON object on stdout, schema:
```json
{
  "request": { "artifactType": "skill", "name": "code-reviewer", "targets": ["claude"], "scope": "project", "mode": "symlink", "force": false, "dryRun": false },
  "sourceCommitSha": "abc123…",
  "computedHash": "sha256:…",
  "lockfilePath": "/path/to/aidriven-lock.json",
  "targets": [
    {
      "target": "claude",
      "action": "install_new",
      "finalMode": "symlink",
      "readPath": "/proj/.claude/skills/code-reviewer",
      "canonicalPath": "/proj/.agents/skills/code-reviewer",
      "error": null
    }
  ],
  "success": true,
  "exitCode": 0
}
```
On error the same shape is produced with `success: false`, a non-zero `exitCode`, and per-target `error` strings (Constitution §VIII: structured output includes errors).

### `--dry-run`

Prints the same shape (text or JSON) as a real run but with each target's `action` reflecting what *would* happen and a top-level `dryRun: true` flag. No filesystem writes occur. The lockfile is not modified.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success — every target installed, updated, or already up to date |
| `1` | Generic failure — at least one target failed (FR-036) |
| `2` | Usage error — invalid argument, mutually exclusive flags, unknown target/type |
| `3` | Network error — manifest, SHA, or tarball unreachable after retries |
| `4` | Integrity error — checksum mismatch (FR-024) |
| `5` | Conflict — foreign/modified content present, `--force` not given (FR-031) |
| `6` | Auto-detection failure — zero or multiple targets detected with no `--ai` (FR-016, FR-017) |

Codes are stable and documented; tests assert each path under `tests/cli/install/test_cli_exit_codes.py` (G7).

---

## Help text

`aidriven install --help` MUST:
- List every flag with a one-line description (Constitution §II).
- Show one example: `aidriven install skill code-reviewer --ai claude`.
- Show one multi-target example: `aidriven install skill code-reviewer --ai claude --ai copilot`.
- Mention the default scope (`project`) and default mode (symlink).
- Be free of jargon — no internal module names.

---

## Library equivalent

Every CLI invocation maps 1:1 to a single library call:

```python
from aidriven.install import install_artifact, InstallRequest, ArtifactType, Scope, InstallMode

result = install_artifact(InstallRequest(
    artifact_type=ArtifactType.SKILL,
    name="code-reviewer",
    targets=("claude", "copilot"),
    scope=Scope.PROJECT,
    mode=InstallMode.SYMLINK,
    force=False,
    dry_run=False,
    assume_yes=False,
))
```

Constitution §I: the CLI `_install_cmd.py` MUST contain no logic beyond argparse → `InstallRequest` → `install_artifact()` → output formatting.
