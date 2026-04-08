# Phase 0 Research: CLI Artifact Install

**Date**: 2026-04-07
**Spec**: [spec.md](spec.md)
**Reference**: [reference-analysis.md](reference-analysis.md) (vercel-labs/skills v1.4.9 inspection)

This document captures the design research consolidating the spec's resolved clarifications, the `vercel-labs/skills` reference analysis, and the constitution gates into actionable decisions. There are **no remaining `NEEDS CLARIFICATION` items** — all five clarification questions have been answered in spec.md (Session 2026-04-07).

---

## 1. Decision: Adopt the `vercel-labs/skills` canonical-directory + symlink model

**Decision**: Files are written once at `.agents/skills/<name>/` (project) or `~/.agents/skills/<name>/` (user) and exposed to AI-target-specific read paths via directory symlinks. Copy mode (`--copy`) is opt-in.

**Rationale**: `.agents/skills/` is the de facto industry-standard location read by 40+ agents (Copilot, Cursor, Codex CLI, Kilo Code, Warp). Storing once + symlinking avoids duplication, keeps content consistent across targets, and matches the pattern that downstream tooling already expects. Single source of truth simplifies idempotency, hashing, and updates.

**Alternatives considered**:
- *Direct install per target* (no canonical) — duplicates content, breaks "one edit, all targets" semantics, makes hash comparison ambiguous. Kept as opt-in `--copy`.
- *Symlink farm with one symlink per file* — more complex, more I/O, no benefit over a directory symlink.
- *Hard links* — not portable on Windows across drives; semantics confusing on edit.

---

## 2. Decision: Single trusted source — `aidriven-resources` only (no arbitrary repos)

**Decision**: The CLI fetches exclusively from `aidriven-resources`. No source-URL parsing, no per-install source argument.

**Rationale**: Constitution §IV ("Artifact sources MUST be validated") plus the spec's explicit non-goal of authentication and private repos. A single trusted source dramatically reduces the attack surface and lets us skip the entire `source-parser.ts` complexity that vercel-labs/skills carries (8+ URL formats).

**Alternatives considered**:
- *Pluggable source adapters in v1* — premature; the constitution's Extensibility Rules require an adapter interface eventually, but adding one now without a real second source would be over-engineering. The `_github.py` module is structured so a future `_source_base.py` abstraction can be extracted without rewriting callers.

---

## 3. Decision: Fetch via GitHub repository tarball at a pinned commit SHA

**Decision** (clarification Q1 → option E): Download `https://github.com/<owner>/aidriven-resources/archive/<sha>.tar.gz` for the resolved commit SHA, then extract only the requested skill subdirectory.

**Rationale**: One HTTP call per install; one SHA-256 over the whole archive (clean fit for FR-024); no per-skill publishing pipeline; no `git` binary dependency; the commit SHA is already first-class in the lockfile (`sourceCommitSha`). Python stdlib `tarfile` handles `.tar.gz` natively.

**Alternatives considered**:
- *Per-file fetch via Contents API* (vercel-labs/skills's approach) — N HTTP calls, per-file checksums in the manifest, more rate-limit pressure, more complex caching. Justified there because they support arbitrary repos; not justified for a single trusted source.
- *Per-skill `.tar.gz` published to GitHub Releases* — requires a publishing pipeline in `aidriven-resources` and an additional release step per skill update. Higher friction with no clear benefit over the on-the-fly archive endpoint.
- *Shallow `git clone`* — adds a `git` binary dependency, slower for a single skill, harder to integrity-check.

---

## 4. Decision: Manifest is `manifest.json` at the repo root, fetched via raw.githubusercontent.com

**Decision** (clarification Q2 → option A): A single JSON file `manifest.json` lives at the root of `aidriven-resources`. The CLI fetches it via `https://raw.githubusercontent.com/<owner>/aidriven-resources/<sha>/manifest.json`.

**Rationale**: JSON is parseable with the Python stdlib (no extra deps — Constitution §VII). Root placement is the conventional discovery point. Using `raw.githubusercontent.com` with a pinned SHA gives byte-stable retrieval and bypasses the GitHub Contents API rate limit (5000/hr authenticated, 60/hr unauthenticated for Contents; raw is generally not subject to the same low limits).

**Manifest schema** (versioned per FR-022): see [contracts/manifest.schema.json](contracts/manifest.schema.json).

**Alternatives considered**:
- *YAML* — requires a dependency (PyYAML); violates stdlib-only.
- *Per-artifact-type manifest* (`manifests/skills.json`, etc.) — premature decomposition; a single file is simpler to fetch, cache, and validate.
- *Nested `skills/manifest.json`* — adds path coupling for no benefit.

---

## 5. Decision: Resolve commit SHA once per run via the GitHub API

**Decision** (clarification Q3 → option A): At the start of each run the CLI calls `GET https://api.github.com/repos/<owner>/aidriven-resources/commits/<default-branch>` to obtain the current HEAD SHA. That SHA is then used for *both* the manifest fetch and the tarball fetch in the same run.

**Rationale**: Guarantees the manifest and the bundle come from the *same* commit (no race window where the manifest is updated mid-run). The resolved SHA is recorded in `aidriven-lock.json` as `sourceCommitSha`, enabling byte-identical reproducibility (SC-003).

**Operational notes**:
- Unauthenticated GitHub API allows 60 requests/hour per IP. With one API call per `aidriven install` invocation this is comfortably within limits for normal interactive use. CI users hitting the limit can be told to set `GITHUB_TOKEN` in a future iteration (out of scope here).
- Manifest TTL cache (FR-028, default 1h) caches the *manifest content keyed by SHA*, not the SHA itself. The SHA is re-resolved per run unless `--force` skips the cache and we still want a fresh resolution.

**Alternatives considered**:
- *Read SHA from inside the manifest* — chicken-and-egg: you need a SHA to fetch the manifest from a pinned URL.
- *Use the `main` branch ref directly without pinning* — race condition between manifest fetch and tarball fetch; non-reproducible.
- *Maintain a `latest` git tag* — extra publishing step in `aidriven-resources`; no benefit.

---

## 6. Decision: Network retry policy — 3 attempts, exponential backoff, transient-only

**Decision** (clarification Q4 → option B): All HTTP requests (SHA resolution, manifest fetch, tarball fetch) retry up to 3 times with backoff `1s, 2s, 4s` on transient failures: connection/network errors, HTTP 5xx, HTTP 429. Other 4xx responses fail fast.

**Rationale**: Balances resilience against flaky networks and brief rate-limit windows with predictable CLI latency. Failing fast on 4xx (other than 429) avoids retrying genuine "not found" or "bad request" errors that will never succeed.

**Implementation note**: Implemented in `_http.py` as a small wrapper around `urllib.request.urlopen` with `ssl.create_default_context()` (HTTPS-only by URL-scheme assertion per FR-025). No `requests` dependency.

---

## 7. Decision: Artifact-name validation — `^[a-z][a-z0-9-]{0,63}$`

**Decision** (clarification Q5 → option A): The CLI rejects `<artifact-name>` arguments not matching `^[a-z][a-z0-9-]{0,63}$` *before* any network call. After local validation, the name is also validated against the manifest (FR-003).

**Rationale**: Prevents path-traversal and shell-quoting issues; matches `vercel-labs/skills` and most package-manager conventions; portable across Windows/macOS/Linux directory naming; bounded length avoids pathological inputs.

---

## 8. Decision: SHA-256 of sorted file contents as the canonical content hash

**Decision**: `computedHash` = `sha256( concat( for path in sorted(rel_paths): path_bytes + 0x00 + file_bytes + 0x00 ) )`. Stored in lockfile entries; used for idempotency (FR-030) and update detection (FR-031).

**Rationale**: Source-agnostic — does not depend on GitHub tree SHAs (vercel-labs/skills issue #386). Deterministic, survives re-download, allows comparison without re-fetching. Sorting by relative path makes ordering implementation-independent. Including the path inside the hash input prevents two skills with rearranged file names from colliding.

**Alternatives considered**:
- *Hash the tarball directly* — only valid immediately after download; cannot be recomputed from disk after extraction.
- *Hash a manifest of (path, file-hash) pairs* — equivalent in practice; chosen form is simpler.

---

## 9. Decision: Lockfile design — one per scope, schema-versioned, deterministic project file

**Decision**:
- **Project lockfile**: `<project-root>/aidriven-lock.json`. Schema `version: 1`. Skills keyed by name, sorted alphabetically. No timestamps. Designed to be committed to VCS.
- **User state file**: `~/.cache/aidriven/install-records.json`. Same schema; MAY include timestamps for user convenience; not committed.
- **Migrations**: Future schema bumps MUST migrate or warn — never silently discard entries (lesson from vercel-labs/skills issue #542).

**Rationale**: Avoids the dual-lockfile fragmentation that has plagued vercel-labs/skills (issues #542, #775). One file per scope, self-contained for that scope, no cross-reading.

**Schema**: see [contracts/lockfile.schema.json](contracts/lockfile.schema.json).

---

## 10. Decision: Symlink semantics & Windows fallback

**Decision**:
- **POSIX**: `os.symlink(canonical_dir, target_read_path, target_is_directory=True)`.
- **Windows**: Same call. On modern Python + Windows 10+, this creates a directory symlink when developer mode is enabled, and otherwise raises `OSError`. On failure for any target, fall back to **copy mode for that target only** and emit a warning. The other targets in the same run are unaffected.
- **Idempotency**: If the read path is already a symlink pointing at the canonical dir, no action. If it points elsewhere, treat as conflict per FR-031.
- **Pre-create check**: The canonical directory MUST be populated before any symlinks are created (vercel-labs/skills issue #537).

**Rationale**: Stdlib-only, no `ctypes` or `mklink` shell-out needed. Per-target fallback preserves "succeed where possible" semantics and matches FR-008b.

---

## 11. Decision: Tarball extraction safety

**Decision**: Use `tarfile.open(mode='r:gz')`. For each member:
1. Reject any member whose normalized path contains `..` or starts with `/` or contains a drive letter.
2. Resolve the destination as `(extract_root / member_path).resolve()` and assert it is within `extract_root.resolve()`.
3. Reject symlink/hardlink members (skills are plain files; links inside the archive are not needed and would let an attacker escape the extraction root).
4. On Python 3.12+, also pass `filter='data'` to `tarfile.extractall` for defence in depth (PEP 706).

**Rationale**: Constitution G9 (path-traversal prevention). Skills are documents; rejecting link members costs nothing and removes a known attack class.

---

## 12. Decision: Caching strategy

**Decision**:
- **Manifest cache**: Stored at `~/.cache/aidriven/manifest/<sha>.json` keyed by SHA. TTL is irrelevant when keyed by SHA (a given SHA's content is immutable), but the *SHA resolution itself* is cached for FR-028's default 1h TTL at `~/.cache/aidriven/manifest/_head.json` (`{sha, expires_at}`). `--force` bypasses both.
- **Tarball cache**: Stored at `~/.cache/aidriven/cache/<sha>.tar.gz`. Reused across multiple skill installs from the same commit. `--force` bypasses.
- **Cache directory**: `pathlib.Path(os.environ.get("AIDRIVEN_CACHE_DIR") or platform_default())`. Platform default per Constitution §IX: `~/.cache/aidriven` on Linux/macOS, `%LOCALAPPDATA%\aidriven\Cache` on Windows. No third-party `platformdirs` dependency — a small in-house function suffices.

**Rationale**: SHA-keyed cache is correct by construction (G17) — there is no stale-data risk because content is immutable per SHA. The 1h TTL applies only to "what is HEAD right now?" which is the only mutable piece.

---

## 13. Decision: Phase boundaries enforced in module layout

**Decision**: The install package mirrors the constitution's five phases:
- **Discover** → not part of v1 install (a future `aidriven list` subcommand).
- **Resolve** → `_github.py` (SHA) + `_manifest.py` (lookup) — no filesystem writes.
- **Preview** → `_planner.py` builds an `InstallPlan` (a pure data structure) and `--dry-run` prints it without invoking `_installer.py`.
- **Install** → `_installer.py` is the only module that writes outside the cache directory.
- **Update** → not in v1; `--force` re-fetch is the v1 mechanism.

**Rationale**: G19 (phase boundary enforcement). Easy to test: a unit test that imports `_planner` and asserts no filesystem writes happen verifies the boundary mechanically.

---

## 14. Decision: AI target registry & extensibility

**Decision**: AI targets are described by a small frozen dataclass list in `_targets.py`:

```python
@dataclass(frozen=True)
class AITarget:
    name: str                       # "claude" | "copilot"
    project_read_path: str          # ".claude/skills" | ".agents/skills"
    user_read_path: str             # ".claude/skills" | ".copilot/skills"
    autodetect_markers: tuple[str, ...]  # filesystem paths that indicate presence

TARGETS: dict[str, AITarget] = {
    "claude": AITarget("claude", ".claude/skills", ".claude/skills", (".claude/",)),
    "copilot": AITarget("copilot", ".agents/skills", ".copilot/skills", (".github/copilot-instructions.md",)),
}
```

The canonical directory is always `.agents/skills` (project) or `~/.agents/skills` (user). A target needs a symlink iff its read path differs from the canonical path for that scope.

**Rationale**: Adding a new AI target is one dict entry — no changes to `_planner.py`, `_installer.py`, `_lockfile.py`, or the CLI. Satisfies FR-011 / SC-007 / Extensibility Rules.

---

## 15. Decision: AI target auto-detection signals

**Decision**: When `--ai` is omitted, auto-detection inspects:
1. Filesystem markers in the resolved project root (per `AITarget.autodetect_markers`).
2. The existing `aidriven.discovery` IDE result as a *secondary* hint (e.g., VS Code presence → Copilot is plausible).
3. If exactly one target is detected → use it (FR-015). Multiple → exit non-zero with the list (FR-016). Zero → exit non-zero (FR-017).

**Rationale**: Filesystem markers are deterministic and cheap. The discovery layer is reused but is *not* the driver — `--ai` is the primary selector per spec lines 19–20.

---

## 16. Decision: Concurrency

**Decision** (per spec assumption): No file locking in v1. Concurrent runs of `aidriven install` on the same skill rely on filesystem-level write semantics for protection. The risk is documented in spec edge cases.

**Rationale**: Concurrent installs are an unlikely edge case for an interactive developer tool; adding a lockfile-based mutex now would be premature complexity. Revisit if reports surface.

---

## Open items for `/speckit.tasks`

None blocking. The plan is complete and ready to drive task generation.
