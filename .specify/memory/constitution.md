<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 (template) → 1.0.0
  Modified principles: N/A (initial ratification)
  Added sections:
    - 10 Core Principles (I–X)
    - Operation Boundaries
    - Extensibility Rules
    - Non-Goals
    - Quality Gates
    - Governance
  Removed sections: All template placeholders replaced
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ compatible (Constitution Check section present)
    - .specify/templates/spec-template.md — ✅ compatible (requirements and scenarios present)
    - .specify/templates/tasks-template.md — ✅ compatible (phased structure aligns)
    - .specify/templates/checklist-template.md — ✅ compatible (generic, adapts per feature)
  Follow-up TODOs: None
-->

# aidriven Constitution

## Core Principles

### I. Library-First

The `aidriven` package MUST be structured as a reusable Python library
first and a CLI second. All artifact discovery, resolution, validation,
download, and installation logic MUST reside in the library layer under
`src/aidriven/` and MUST NOT depend on CLI frameworks, terminal I/O, or
user-facing presentation concerns.

- Every public capability MUST be importable and callable from Python
  code without invoking a CLI process.
- The CLI layer MUST be a thin adapter that delegates to the library,
  translates user input into library calls, and formats library output
  for the terminal.
- The library MUST NOT import from the CLI layer. Dependency direction
  is strictly CLI → library, never the reverse.
- Unit and integration tests MUST exercise the library directly; CLI
  tests exist separately and test argument parsing, output formatting,
  and exit codes.

### II. CLI-First with Excellent UX

The CLI is the primary user interface and MUST deliver a professional,
consistent, and accessible experience.

- Command names, flag names, and argument ordering MUST follow a
  consistent grammar across all subcommands (verb-noun or noun-verb,
  chosen once and applied everywhere).
- `--help` output MUST be clear, complete, and free of jargon. Every
  flag MUST include a one-line description.
- All user-facing messages MUST be actionable: errors MUST say what
  went wrong and what the user can do; warnings MUST explain the risk;
  success messages MUST confirm what happened.
- Defaults MUST be safe. No destructive or surprising action MUST occur
  without explicit user intent.
- Progressive feedback MUST be provided for operations that take more
  than ~500ms: spinners, progress bars, or incremental output.
- Colors, spinners, and other ANSI escape sequences MUST only be
  emitted when stdout is a TTY. The `NO_COLOR` environment variable
  MUST be respected.
- Interactive selectors and prompts MUST be usable with keyboard
  navigation and MUST degrade gracefully when the terminal does not
  support them.

### III. Automation and Scriptability

`aidriven` MUST work as well in scripts, pipelines, and CI as it does
in an interactive terminal.

- All commands MUST accept a `--json` flag that emits structured JSON
  to stdout, suitable for piping to `jq` or programmatic consumption.
- All commands MUST support `--quiet` (suppress non-essential output)
  and `--verbose` (increase diagnostic detail).
- All commands that perform write operations MUST support `--dry-run`
  to preview changes without applying them.
- Exit codes MUST be consistent and documented: `0` for success, `1`
  for general errors, `2` for usage errors, distinct codes for
  specific failure classes where useful.
- The tool MUST NOT block waiting for interactive input when stdin is
  not a TTY. In non-interactive mode, any operation that would require
  user confirmation MUST either fail with a clear error or proceed
  only if an explicit `--yes` or `--force` flag is provided.
- stdin/stdout pipelines MUST be supported: command output MUST be
  composable with standard Unix tools.

### IV. Installation Safety

Installing AI artifacts into a user's project is a trust-sensitive
operation. `aidriven` MUST treat every installation as a potential
vector for harm and enforce defensive defaults.

- Artifact sources MUST be validated. The tool MUST verify that
  artifacts originate from a declared, trusted source before
  installation. Unknown or unverified sources MUST be rejected unless
  the user explicitly opts in.
- Artifact versions MUST be pinned or resolved deterministically.
  Installations MUST be reproducible given the same inputs.
- Overwrites MUST require confirmation. If an artifact or file already
  exists in the target project, the tool MUST NOT overwrite silently.
  Overwriting MUST require explicit `--force` or interactive
  confirmation.
- Path traversal MUST be prevented. Artifact contents MUST NOT be able
  to write outside the declared target directory. All resolved paths
  MUST be validated against the installation root.
- Arbitrary code execution MUST NOT occur as a side effect of
  discovery, resolution, or installation. No post-install hooks, no
  eval, no dynamic code loading from artifact content unless the user
  explicitly opts in to a documented, auditable mechanism.
- Least privilege MUST be preserved. The tool MUST NOT request or
  require elevated permissions beyond what the specific operation
  needs.

### V. Idempotency and Reliability

- Running the same install command twice with the same inputs MUST
  produce the same result. The second invocation MUST detect that the
  artifact is already present and either skip or confirm, never
  corrupt.
- Failed operations MUST leave the project in a recoverable state.
  Partial writes MUST be cleaned up or clearly reported. Where
  feasible, operations SHOULD be atomic (write to a temporary
  location, then move into place).
- Before making changes, the tool MUST detect and communicate the
  current project state and the intended changes. `--dry-run` MUST
  show the full change set without applying it.
- Rollback SHOULD be supported where feasible. At minimum, the tool
  MUST report enough information for the user to manually reverse an
  operation.

### VI. Compatibility and Portability

- `aidriven` MUST behave consistently on Linux, macOS, and Windows.
  All CI pipelines SHOULD include at least Linux; Windows and macOS
  SHOULD be tested when platform-specific code paths exist.
- File paths MUST use `pathlib.Path` or equivalent abstractions. Raw
  string concatenation for paths is prohibited.
- Text encoding MUST default to UTF-8. Encoding assumptions MUST be
  explicit, never implicit.
- File permissions MUST be handled in a cross-platform manner.
  Operations that depend on Unix-specific permission semantics MUST
  degrade gracefully or document limitations on Windows.
- Line endings MUST be handled consistently. The `.editorconfig`
  enforces LF; the tool MUST NOT introduce CRLF artifacts.

### VII. Engineering Quality

The following engineering practices are non-negotiable for all code
under `src/aidriven/` and `tests/`:

- **Static typing**: All code MUST pass `mypy --strict`. No `# type:
  ignore` without an inline justification comment.
- **Linting and formatting**: All code MUST pass `ruff check` and
  `ruff format --check` with the project configuration. Pre-commit
  hooks MUST enforce this on every commit.
- **Unit tests**: Every library module MUST have corresponding unit
  tests under `tests/unit/`. Tests MUST be fast, isolated, and
  deterministic.
- **Integration tests**: Interactions between modules, external
  sources, and the filesystem MUST be covered under
  `tests/integration/`.
- **CLI tests**: Command parsing, output formatting, and exit codes
  MUST be tested under `tests/cli/`.
- **Coverage**: Coverage MUST be tracked. The coverage floor MUST be
  raised as the codebase matures; it MUST NOT decrease without
  explicit justification.
- **Documentation**: Public APIs MUST have docstrings. Usage
  documentation MUST include realistic, runnable examples.
- **Dependencies**: New runtime dependencies MUST be justified. The
  dependency count MUST remain minimal. Dev dependencies are
  acceptable and tracked in `[dependency-groups] dev`.

### VIII. Observability and Diagnostics

- Log output MUST use Python's `logging` module. Log levels MUST be
  meaningful: `DEBUG` for internal tracing, `INFO` for user-relevant
  events, `WARNING` for recoverable issues, `ERROR` for failures.
- Error messages MUST guide correction: what failed, why, and what to
  try next. Stack traces MUST NOT appear in normal output; they MUST
  be available via `--verbose` or `--debug`.
- Structured output (`--json`) MUST include error details, not just
  success payloads.
- Telemetry MUST NOT exist unless implemented as explicit, documented,
  off-by-default opt-in. No silent phone-home, no usage tracking
  without consent.

### IX. Perceived Performance

- CLI startup MUST remain fast. Lazy imports MUST be used for heavy
  dependencies. Top-level imports MUST NOT trigger network I/O,
  filesystem scans, or expensive initialization.
- Catalog listings and artifact searches MUST feel responsive. If a
  network call is required, progressive output MUST indicate activity
  within 500ms.
- Local caching MAY be used to accelerate repeated operations (catalog
  metadata, resolved versions) but MUST NOT serve stale data silently.
  Cache invalidation MUST be correct, and `--no-cache` MUST bypass it
  entirely.
- Cache files MUST be stored in a platform-appropriate location (e.g.,
  XDG or `platformdirs`) and MUST NOT pollute the user's project
  directory.

### X. Governance

- Every architecture decision, feature specification, implementation
  plan, and code review MUST be validated against this constitution.
- A feature or design that violates a constitutional principle MUST
  NOT proceed without explicit justification documented in the
  relevant spec or plan, AND a formal review of whether the
  constitution itself should be amended.
- Amendments to this constitution MUST be versioned, documented, and
  reviewed. No silent drift.

## Operation Boundaries

`aidriven` operates through five distinct phases. Each phase MUST have
a clear entry point, output contract, and failure mode.

| Phase       | Responsibility                                      | MUST NOT                                    |
|-------------|-----------------------------------------------------|---------------------------------------------|
| **Discover**| Browse and search catalogs for available artifacts   | Modify the user's project                   |
| **Resolve** | Determine exact version, source, and dependencies    | Download artifact content                   |
| **Preview** | Show what will change before applying                | Write to the filesystem                     |
| **Install** | Download and place artifacts into the target project | Skip validation or overwrite without consent|
| **Update**  | Upgrade installed artifacts to newer versions        | Change artifacts the user did not select    |

- Phase boundaries MUST be enforced in the library API. A `discover()`
  call MUST NOT trigger side effects belonging to `install()`.
- Each phase MUST be independently invocable from both the library and
  the CLI.

## Extensibility Rules

- **New artifact types** (e.g., beyond skills, agents, rules, specs)
  MUST be added through a defined registry or plugin interface. Adding
  a new type MUST NOT require modifying core resolution or installation
  logic.
- **New sources/remotes** (e.g., a private registry, a Git repository,
  a local directory) MUST be added through a source adapter interface.
  Each adapter MUST implement the same discovery and resolution
  contract. Adding a new source MUST NOT require changes to the CLI
  layer.
- Extensibility MUST NOT compromise safety. Third-party plugins or
  adapters MUST NOT bypass validation, path traversal checks, or
  overwrite protections.

## Non-Goals

The following are explicitly out of scope for `aidriven`. Proposals
that move toward these areas MUST be rejected unless the constitution
is formally amended.

- **Runtime execution of artifacts**: `aidriven` installs artifacts
  into projects. It MUST NOT execute, interpret, or host them.
- **Artifact authoring or publishing**: `aidriven` is a consumer tool.
  Authoring and publishing workflows belong to separate tooling.
- **Project scaffolding**: `aidriven` installs discrete artifacts, not
  entire project templates. It is not `cookiecutter` or `copier`.
- **Dependency management for the user's project**: `aidriven` manages
  its own dependencies. It MUST NOT modify the user's `pyproject.toml`,
  `package.json`, or equivalent unless an artifact explicitly declares
  such a requirement and the user confirms.
- **Language-specific code generation**: Artifacts are delivered as-is.
  `aidriven` MUST NOT transpile, compile, or transform artifact
  content.
- **Cloud services or hosted backends**: `aidriven` is a local CLI
  tool. It MAY fetch from remote catalogs but MUST NOT require a
  proprietary backend service to function.

## Quality Gates

Every specification, plan, task list, and implementation MUST pass
these gates. Each gate is binary (pass/fail) and auditable.

| #  | Gate                          | Criterion                                                                                              |
|----|-------------------------------|--------------------------------------------------------------------------------------------------------|
| G1 | Library independence          | All new features are callable from Python without CLI. Verified by unit tests that import only library. |
| G2 | CLI thin-layer                | CLI modules contain no business logic. Verified by code review: no domain logic in CLI files.          |
| G3 | TTY safety                    | No ANSI codes emitted when stdout is not a TTY. Verified by CLI test with redirected output.           |
| G4 | Non-interactive mode          | All commands complete without interaction when stdin is not a TTY. Verified by CI (no TTY).            |
| G5 | JSON output                   | `--json` produces valid, parseable JSON for every command. Verified by CLI test.                       |
| G6 | Dry-run fidelity              | `--dry-run` produces output describing changes without applying them. Verified by filesystem assertion. |
| G7 | Exit codes                    | Documented exit codes are returned correctly. Verified by CLI test.                                    |
| G8 | Overwrite protection          | Existing files are never overwritten without `--force` or confirmation. Verified by integration test.  |
| G9 | Path traversal prevention     | Artifact paths that escape the target root are rejected. Verified by unit test with malicious input.   |
| G10| No implicit code execution    | Installation does not eval, exec, or import artifact content. Verified by code review and test.        |
| G11| Idempotent install            | Running install twice produces the same filesystem state. Verified by integration test.                |
| G12| Cross-platform paths          | All path operations use `pathlib`. No raw string concatenation. Verified by grep + code review.        |
| G13| mypy strict                   | `mypy --strict` passes with zero errors. Verified by CI.                                               |
| G14| ruff clean                    | `ruff check` and `ruff format --check` pass. Verified by CI and pre-commit.                           |
| G15| Test coverage floor           | Coverage does not decrease. Verified by CI coverage report comparison.                                 |
| G16| Startup latency               | `aidriven --version` completes in <500ms on a cold start. Verified by benchmark test.                  |
| G17| Cache correctness             | Cached data is never served when the source has changed. Verified by integration test.                 |
| G18| No telemetry without consent  | No network calls occur unless the user initiates an operation. Verified by network-isolated test.      |
| G19| Phase boundary enforcement    | Discovery operations do not mutate. Install operations do not skip validation. Verified by unit test.  |
| G20| Constitution compliance       | Spec, plan, and task artifacts reference applicable gates. Verified by review checklist.                |

## Governance

- This constitution is the supreme authority for all design and
  implementation decisions in `aidriven`. When a conflict arises
  between this document and any other artifact (spec, plan, task list,
  code comment, or documentation), this constitution prevails.
- All pull requests and code reviews MUST include a constitution
  compliance check. Reviewers MUST verify that changes do not violate
  any principle or quality gate.
- Amendments to this constitution MUST follow semantic versioning:
  - **MAJOR**: Removal or redefinition of a principle (backward-
    incompatible governance change).
  - **MINOR**: Addition of a new principle or material expansion of
    existing guidance.
  - **PATCH**: Clarifications, typo fixes, non-semantic refinements.
- Every amendment MUST be documented with a rationale and MUST update
  the version and date below.
- Complexity MUST be justified. Any deviation from these principles
  MUST be documented in the relevant spec or plan with a clear
  rationale and a reference to the specific principle being overridden.

**Version**: 1.0.0 | **Ratified**: 2025-04-04 | **Last Amended**: 2025-04-04
