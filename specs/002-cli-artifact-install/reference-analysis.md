# Reference Analysis: vercel-labs/skills → aidriven spec

**Date**: 2026-04-07
**Source**: https://github.com/vercel-labs/skills (v1.4.9, MIT, 13.3k stars)
**Inspected files**: `src/installer.ts`, `src/skill-lock.ts`, `src/local-lock.ts`, `src/agents.ts`, `src/source-parser.ts`, `src/blob.ts`, `src/install.ts`, `src/types.ts`, `src/update-source.ts`, README
**Issues inspected**: #542, #775, #537, #421, #278, #11, #165

---

## 1. Adopt (patterns to take directly)

### Canonical `.agents/skills/` directory
Skills CLI stores all project-scope skills at `.agents/skills/<name>/`. GitHub Copilot's `skillsDir` is defined as `.agents/skills/` — it reads directly from this path. 40+ agents share this location (Copilot, Cursor, Codex, Kilo Code, Warp, etc.). This is the industry-standard universal location.

**Decision**: Replace `.github/skills/` with `.agents/skills/<name>/` as the canonical project-scope directory. Copilot reads directly from it; Claude gets a symlink from `.claude/skills/<name>/`.

### Symlink from target-specific directories
In `installer.ts`, the CLI copies files to `.agents/skills/<name>/` (canonical), then creates symlinks from agent-specific directories (e.g., `.claude/skills/<name>/`) to the canonical. Universal agents (those whose `skillsDir` IS `.agents/skills/`) skip symlinks — they read the canonical directly.

**Decision**: Adopt symlink-first model as default. Files are stored once; each target that doesn't read the canonical gets a symlink.

### Copy mode as opt-in alternative
Skills CLI supports `--copy` which writes directly to each agent's read directory without a canonical intermediate. Useful when symlinks are problematic (restricted environments, Windows without developer mode, team preferences).

**Decision**: Add `--copy` flag to `aidriven install`.

### VCS-friendly project lockfile
`local-lock.ts` (`skills-lock.json`) is designed for git: sorted alphabetically by skill name for deterministic output, no timestamps to minimize merge conflicts, minimal fields (source, ref, sourceType, computedHash). Intended to be committed to version control.

**Decision**: Redesign the project-scope install record following these principles. Rename to `aidriven-lock.json` at project root (visible, like `package-lock.json`).

### SHA-256 content hash from disk files
Local lock's `computedHash` is a SHA-256 computed from all file contents sorted by relative path. Source-agnostic (no dependency on GitHub API), deterministic, survives re-download from any source.

**Decision**: Adopt SHA-256 of sorted file contents as the hash mechanism for all idempotency and integrity checks.

### Path traversal protection
`installer.ts` includes `isPathSafe()` to validate that resolved paths don't escape expected directories.

**Decision**: Add path safety validation (already implicit in aidriven's deterministic path model, but should be explicit).

---

## 2. Adapt (patterns to modify for aidriven)

### Single trusted source vs arbitrary repos
Skills CLI parses any GitHub/GitLab/git URL/shorthand (`source-parser.ts` handles 8+ formats). aidriven uses only `aidriven-resources` as a controlled source with a curated manifest.

**Decision**: Keep aidriven's simplified single-source model. No need for complex source parsing.

### Dual lockfile → single lockfile per scope
Skills CLI has TWO lockfiles: global (`~/.agents/.skill-lock.json`, v3, rich metadata) and project (`./skills-lock.json`, v1, minimal). They track different fields and different commands read different files — this caused #542 (15 upvotes, still not fixed in main branch). `check`/`update` only read the global lock, making project-level skills invisible.

**Decision**: ONE lockfile per scope. Project: `aidriven-lock.json`. User: `~/.cache/aidriven/install-records.json`. Each is self-contained for its scope. No cross-reading needed.

### Universal agent concept → explicit "reads canonical" flag
Skills CLI marks agents as "universal" when their `skillsDir` equals `.agents/skills/` — these skip symlinks silently. This is implicit and confusing.

**Decision**: Make this explicit in the path table: Copilot at project scope reads the canonical directory directly (column: "Linking: none"), Claude needs a symlink.

### AI target naming
Skills CLI uses `github-copilot`, `claude-code`. aidriven uses shorter `claude`, `copilot`.

**Decision**: Keep aidriven's names (already decided in earlier spec iteration).

### Blob/Tree API download
Skills CLI uses a 3-step process: GitHub Trees API → raw.githubusercontent.com (frontmatter) → skills.sh/api/download (cached snapshots). This is an optimization for arbitrary repos.

**Decision**: Keep aidriven's manifest-driven download from a single trusted source.

---

## 3. Avoid (antipatterns and known bugs)

### Dual lockfile fragmentation (#542, #775)
`check`/`update` commands only read the global lock, ignoring the project lock. Project-level skills (the default!) are invisible to update commands. 15 upvotes, multiple reports, fix PR still open.

**Lesson**: Never split install state across two files that should be queried together. aidriven uses one file per scope.

### Silent lock migration wiping entries (#542)
Global lock version upgrade (v1/v2 → v3) silently discards all entries with `{ skills: {} }` and no warning. Users lose all tracking data silently.

**Lesson**: Always warn or migrate on schema changes. aidriven lockfile schema includes a version field; future schema changes MUST migrate data or warn.

### Aggressive rm-rf before install (`cleanAndCreateDirectory`)
Skills CLI removes the entire skill directory before every reinstall with no content comparison. Modified files, extra files — all deleted without warning.

**Lesson**: Compare content hashes first; only overwrite when needed. Already addressed by FR-030/031, which compare before overwriting and protect foreign files.

### No integrity verification during download
Skills CLI downloads via raw.githubusercontent.com and blob API with no checksum validation of downloaded content. Hash is used only for update detection, not integrity verification.

**Lesson**: Always verify checksums. Already addressed by FR-024 (mandatory checksum verification).

### Global install leaving agent dir missing (#537)
Canonical directory created but symlink targets not verified as existing.

**Lesson**: Verify canonical directory exists and is populated before creating symlinks. If canonical write fails, no symlinks should be created.

### Update only works for GitHub sources (#386)
Hash comparison uses GitHub-specific tree SHA, breaking for non-GitHub sources.

**Lesson**: Compute hashes from disk file contents (source-agnostic), not from API-specific metadata. Already ensured by adopting SHA-256 from disk files.

---

## 4. Updated Command Semantics

```
aidriven install <artifact-type> <artifact-name> [--ai <target>]... [--scope project|user] [--force] [--copy]
```

New flag: `--copy` — place files directly in each AI target's read directory instead of using canonical + symlink.

---

## 5. Updated Installation Model

**Symlink mode (default):**
1. Download skill files from `aidriven-resources`
2. Place files at canonical directory: `.agents/skills/<name>/` (project) or `~/.agents/skills/<name>/` (user)
3. For each AI target whose read path differs from canonical, create a directory symlink from the read path to the canonical directory
4. On Windows, use directory junctions as symlink equivalent; fall back to copy if junction creation fails

**Copy mode (`--copy`):**
1. Download skill files from `aidriven-resources`
2. Place independent copies directly at each AI target's read path
3. No canonical directory, no symlinks

**Path table (symlink mode — default):**

| AI Target | Scope   | Canonical Dir                | Target Read Path             | Linking               |
|-----------|---------|------------------------------|------------------------------|-----------------------|
| claude    | project | `.agents/skills/<name>/`     | `.claude/skills/<name>/`     | symlink → canonical   |
| claude    | user    | `~/.agents/skills/<name>/`   | `~/.claude/skills/<name>/`   | symlink → canonical   |
| copilot   | project | `.agents/skills/<name>/`     | *(reads canonical directly)* | none                  |
| copilot   | user    | `~/.agents/skills/<name>/`   | `~/.copilot/skills/<name>/`  | symlink → canonical   |

**Path table (copy mode):**

| AI Target | Scope   | Install Dir                  |
|-----------|---------|------------------------------|
| claude    | project | `.claude/skills/<name>/`     |
| claude    | user    | `~/.claude/skills/<name>/`   |
| copilot   | project | `.agents/skills/<name>/`     |
| copilot   | user    | `~/.copilot/skills/<name>/`  |

---

## 6. Updated Lockfile Design

**Project lockfile**: `<project-root>/aidriven-lock.json`

Design principles (from skills CLI's `local-lock.ts`, avoiding its dual-lock mistakes):
- Located at project root (visible, like `package-lock.json`)
- Sorted alphabetically by skill name (deterministic, clean diffs)
- No timestamps (minimizes merge conflicts)
- Content hash computed via SHA-256 of all file contents (sorted by relative path)
- Designed to be committed to version control
- Supports `aidriven install` (restore from lockfile) in future iterations

```json
{
  "version": 1,
  "skills": {
    "code-reviewer": {
      "source": "aidriven-resources",
      "sourceCommitSha": "abc123",
      "computedHash": "sha256:...",
      "targets": ["claude", "copilot"],
      "scope": "project",
      "installMode": "symlink"
    }
  }
}
```

**User state file**: `~/.cache/aidriven/install-records.json`
- Same schema but MAY include timestamps for user convenience
- Not committed to VCS
- Used exclusively for user-scope installations

---

## 7. Updated Functional Requirements

Changes to existing FRs:

| FR | Change | Rationale |
|----|--------|-----------|
| FR-001 | Add `--copy` flag | Symlink/copy mode selection |
| FR-008 | Rewrite path table with canonical + target + linking columns | Canonical model |
| FR-009 | Rewrite rationale: `.agents/skills/` is canonical (industry standard, read by 40+ agents) | Replaces `.github/skills/` rationale |
| New FR-008a | Define canonical directory concept | Core installation model |
| New FR-008b | Define symlink vs copy installation modes | Installation mode semantics |
| FR-029 | Update for canonical model (place at canonical, then symlink) | Canonical model |
| FR-030 | Specify SHA-256 from sorted file contents | Deterministic hash |
| FR-031 | Foreign file check at canonical path in symlink mode | Canonical model |
| FR-032 | Rewrite: VCS-friendly lockfile at project root | Lockfile redesign |
| FR-033 | Add install mode to success summary | Completeness |

---

## 8. Updated Edge Cases

Add to existing list:

- What happens when the OS does not support symlinks (e.g., Windows without developer mode)?
- What happens when a symlink already exists at the target path pointing to a different location?
- What happens when the canonical directory is deleted but symlinks still reference it?
- What happens when `--copy` is used for one install and the same skill is later installed without `--copy` (mode switch)?
- What happens when the user modifies files in the canonical directory and then runs install for a new AI target (symlinks would expose modified content)?

---

## 9. Updated Acceptance Criteria

| ID | Change |
|----|--------|
| SC-005 | Update: replace `.github/skills/` with `.agents/skills/` for Copilot project scope |
| New SC-008 | In symlink mode, installing for multiple AI targets creates exactly one copy of skill files (at canonical) plus symlinks — verified by checking file identity |
| New SC-009 | The project lockfile `aidriven-lock.json` produces deterministic output (sorted keys, no timestamps) suitable for VCS |
