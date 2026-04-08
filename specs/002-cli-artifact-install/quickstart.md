# Quickstart: `aidriven install`

**Date**: 2026-04-07
**Audience**: Developers integrating `aidriven` into a project, and reviewers verifying the feature end to end.

This walkthrough exercises every priority user story (US1–US5) plus the dry-run and `--json` paths from the CLI contract. It assumes `aidriven` is installed and on `$PATH`, and that `https://github.com` is reachable.

---

## 1. US1 — Install one skill for one AI target (P1)

```bash
cd /path/to/your/project
aidriven install skill code-reviewer --ai claude
```

Expected:
- `<project-root>/.agents/skills/code-reviewer/SKILL.md` exists (canonical).
- `<project-root>/.claude/skills/code-reviewer` is a directory symlink → `.agents/skills/code-reviewer`.
- `<project-root>/aidriven-lock.json` contains a `code-reviewer` entry with `source: aidriven-resources`, a 40-char `sourceCommitSha`, a `sha256:` `computedHash`, `targets: ["claude"]`, `scope: "project"`, `installMode: "symlink"`.
- Exit code `0`.

Re-run the same command — exit code `0`, stdout reports `already up to date`, no file changes (idempotency, FR-030, G11).

---

## 2. US2 — Install one skill for multiple AI targets (P2)

```bash
aidriven install skill code-reviewer --ai claude --ai copilot
```

Expected:
- `.agents/skills/code-reviewer/` populated once.
- `.claude/skills/code-reviewer` is a symlink to canonical.
- `.copilot/` is **not** created at project scope — at project scope Copilot reads `.agents/skills/` directly (FR-009).
- Lockfile entry's `targets` is `["claude", "copilot"]` (sorted).

---

## 3. US3 — Install at user scope (P3)

```bash
aidriven install skill code-reviewer --ai claude --scope user
```

Expected:
- `~/.agents/skills/code-reviewer/` populated.
- `~/.claude/skills/code-reviewer` is a symlink to it.
- The state is recorded in `~/.cache/aidriven/install-records.json`, **not** in the project lockfile.

---

## 4. US4 — Force re-fetch (P4)

```bash
aidriven install skill code-reviewer --ai claude --force
```

Expected:
- Cache bypassed; tarball re-downloaded; SHA-256 verified against the manifest (FR-024).
- If remote content changed → `updated code-reviewer`.
- If content unchanged → `already up to date` (after re-fetch and re-hash).
- Exit code `0`.

Tamper test (integrity, FR-024 / exit code 4): manually corrupt the cached tarball before a `--force` run with a wrong manifest checksum → expect exit code `4` and a clear integrity-error message.

---

## 5. US5 — Auto-detect targets (P5)

In a project with `.claude/` present and no `.github/copilot-instructions.md`:

```bash
aidriven install skill code-reviewer
```

Expected:
- Auto-detection finds exactly `claude` and proceeds (FR-015). Output mentions which target was auto-detected.

In a project with both Claude and Copilot markers:

```bash
aidriven install skill code-reviewer
```

Expected:
- Exit code `6`. Stderr lists detected targets and instructs the user to specify `--ai` (FR-016).

---

## 6. Dry-run (Constitution G6)

```bash
aidriven install skill code-reviewer --ai claude --ai copilot --dry-run
```

Expected:
- Plan printed (text or JSON depending on `--json`).
- `aidriven-lock.json` is **not** modified.
- No files appear under `.agents/`, `.claude/`, etc.
- Exit code `0`.

---

## 7. JSON output (Constitution G5)

```bash
aidriven install skill code-reviewer --ai claude --json | jq .
```

Expected:
- Single JSON object on stdout matching the shape in [contracts/cli.md](contracts/cli.md).
- `success: true`, `exitCode: 0`, `targets[0].action` ∈ `{install_new, update, skip_identical}`.
- No spinners or color in stdout regardless of TTY.

---

## 8. Conflict & overwrite protection (G8, FR-031)

```bash
mkdir -p .claude/skills/code-reviewer
echo "manual edit" > .claude/skills/code-reviewer/SKILL.md
aidriven install skill code-reviewer --ai claude
```

Expected:
- Exit code `5`. Message explains the conflict and tells the user to re-run with `--force` or remove the directory.

```bash
aidriven install skill code-reviewer --ai claude --force
```

Expected:
- Overwrite proceeds; lockfile updated; exit code `0`.

---

## 9. Copy mode (FR-008b)

```bash
aidriven install skill code-reviewer --ai claude --ai copilot --copy
```

Expected:
- No `.agents/skills/` directory created.
- `.claude/skills/code-reviewer/` populated with file contents (not a symlink).
- `.github/skills/code-reviewer/` (or whichever read path applies for copilot at project scope per the path table) populated independently.
- Lockfile entry's `installMode` is `"copy"`.

---

## 10. Network failure path (FR-025a, exit code 3)

Disconnect the network or set `AIDRIVEN_GITHUB_API=https://127.0.0.1:1` and run:

```bash
aidriven install skill code-reviewer --ai claude
```

Expected:
- 3 retries with backoff (1s, 2s, 4s) — visible under `--verbose`.
- Final exit code `3` with a human-readable network error message.

---

## Acceptance checklist (maps to spec SCs)

| Item | Verified by |
|------|-------------|
| SC-001 — install one skill in <10s on a normal connection | sections 1, 2 |
| SC-002 — re-run produces no changes when content matches | section 1 (re-run) |
| SC-003 — same `sourceCommitSha` produces byte-identical results | section 1 across machines |
| SC-004 — every error path has non-zero exit + readable message | sections 4, 8, 10 |
| SC-005 — correct path for every (target × scope) combination | sections 1, 2, 3 |
| SC-006 — multi-target single command with per-target reporting | section 2 |
| SC-007 — adding new target/type requires only registry/manifest changes | (architectural — see plan §Project Structure and research §14) |
| SC-008 — symlink mode places exactly one copy + symlinks | section 2 |
| SC-009 — `aidriven-lock.json` is deterministic | section 1 + `tests/unit/install/test_lockfile_determinism.py` |
