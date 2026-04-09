"""CLI install subcommand: argparse → InstallRequest → install_artifact → output."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import NoReturn

from aidriven.install import ArtifactType, InstallMode, InstallRequest, Scope, install_artifact
from aidriven.install._models import InstallResult, PerTargetAction
from aidriven.install._service import (
    EXIT_AUTODETECT_FAILURE,
    EXIT_INTEGRITY_ERROR,
    EXIT_NETWORK_ERROR,
    EXIT_USAGE_ERROR,
    AmbiguousTargetsError,
    NetworkError,
    NoTargetsFoundError,
    UsageError,
)

# Supported artifact types (v1)
_SUPPORTED_TYPES = {t.value for t in ArtifactType}


def _use_color() -> bool:
    """Return True iff ANSI color and glyphs should be emitted."""
    if not sys.stdout.isatty():
        return False
    return not os.environ.get("NO_COLOR")


def _glyph(success: bool, neutral: bool = False, use_color: bool = True) -> str:
    if not use_color:
        return "[ok]" if success else ("[--]" if neutral else "[er]")
    if neutral:
        return "\u2022"  # •
    return "\u2713" if success else "\u2717"  # ✓ / ✗


def _ansi(text: str, code: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def _format_human(result: InstallResult, *, use_color: bool, verbose: bool, quiet: bool) -> str:
    lines: list[str] = []
    for tr in result.target_results:
        action = tr.action_taken
        if action == PerTargetAction.SKIP_IDENTICAL:
            if not quiet:
                glyph = _glyph(True, neutral=True, use_color=use_color)
                msg = f"{glyph} {tr.target_name}  {result.request.name} already up to date"
                if verbose and tr.canonical_path:
                    msg += f" ({result.plan.expected_content_hash[:16]}…)"
                lines.append(msg)
        elif action in (PerTargetAction.INSTALL_NEW, PerTargetAction.UPDATE):
            glyph = _glyph(True, use_color=use_color)
            action_word = "installed" if action == PerTargetAction.INSTALL_NEW else "updated"
            canon = tr.canonical_path
            read = tr.read_path
            detail = f"at {canon}" if canon else f"at {read}"
            if canon and canon != read:
                detail += f" (symlink: {read})"
            elif not canon:
                detail = f"at {read}"
            msg = f"{glyph} {tr.target_name}  {action_word} {result.request.name} {detail}"
            lines.append(msg)
        elif action == PerTargetAction.CONFLICT:
            if not quiet:
                glyph = _glyph(False, use_color=use_color)
                msg = (
                    f"{glyph} {tr.target_name}  refusing to overwrite {tr.read_path} "
                    "(modified or foreign content)\n"
                    "          re-run with --force to overwrite, or remove the directory first."
                )
                lines.append(msg)
        elif action == PerTargetAction.INCOMPATIBLE:
            if not quiet:
                glyph = _glyph(False, use_color=use_color)
                lines.append(
                    f"{glyph} {tr.target_name}  incompatible — {tr.error or 'not supported'}"
                )
        elif tr.error:
            glyph = _glyph(False, use_color=use_color)
            lines.append(f"{glyph} {tr.target_name}  error: {tr.error}")
    return "\n".join(lines)


def _format_json(result: InstallResult) -> str:
    req = result.request
    targets_out = []
    for tr in result.target_results:
        targets_out.append(
            {
                "target": tr.target_name,
                "action": tr.action_taken.value,
                "finalMode": tr.final_mode.value,
                "readPath": str(tr.read_path),
                "canonicalPath": str(tr.canonical_path) if tr.canonical_path else None,
                "error": tr.error,
            }
        )
    payload: dict[str, object] = {
        "request": {
            "artifactType": req.artifact_type.value,
            "name": req.name,
            "targets": list(req.targets),
            "scope": req.scope.value,
            "mode": req.mode.value,
            "force": req.force,
            "dryRun": req.dry_run,
        },
        "sourceCommitSha": result.plan.source_commit_sha,
        "computedHash": result.plan.expected_content_hash,
        "lockfilePath": str(result.lockfile_path),
        "targets": targets_out,
        "success": result.success,
        "exitCode": result.exit_code,
    }
    if req.dry_run:
        payload["dryRun"] = True
    return json.dumps(payload, indent=2)


def _die(message: str, exit_code: int = EXIT_USAGE_ERROR) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aidriven install",
        description=(
            "Install an AI skill from aidriven-resources into your project.\n\n"
            "Examples:\n"
            "  aidriven install skill code-reviewer --ai claude\n"
            "  aidriven install skill code-reviewer --ai claude --ai copilot\n\n"
            "Default scope: project. Default mode: symlink."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("artifact_type", metavar="artifact-type", help="Artifact type (e.g. skill)")
    parser.add_argument(
        "artifact_name", metavar="artifact-name", help="Artifact name (e.g. code-reviewer)"
    )
    parser.add_argument(
        "--ai",
        dest="targets",
        action="append",
        default=[],
        metavar="TARGET",
        help="AI target (claude, copilot). Repeatable. Auto-detected when omitted.",
    )
    parser.add_argument(
        "--scope",
        choices=["project", "user"],
        default="project",
        help="Installation scope (default: project).",
    )
    parser.add_argument("--copy", action="store_true", help="Use copy mode instead of symlink.")
    parser.add_argument(
        "--force", action="store_true", help="Bypass cache and overwrite conflicts."
    )
    parser.add_argument(
        "--dry-run", action="store_true", dest="dry_run", help="Plan only — no writes."
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit JSON output.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Increase diagnostic detail.")
    parser.add_argument("--yes", "-y", action="store_true", help="Bypass interactive confirmation.")
    parser.add_argument(
        "--no-cache", action="store_true", dest="no_cache", help="Bypass fetch cache."
    )
    return parser


def run_install_cmd(argv: list[str] | None = None) -> int:
    """Parse args, run install, emit output, and return exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Mutual exclusion
    if args.quiet and args.verbose:
        parser.error("--quiet and --verbose are mutually exclusive")

    # Validate artifact type
    if args.artifact_type not in _SUPPORTED_TYPES:
        _die(
            f"Unknown artifact type {args.artifact_type!r}. Supported: {sorted(_SUPPORTED_TYPES)}",
            EXIT_USAGE_ERROR,
        )

    use_color = _use_color() and not args.json_output

    # Verbose: enable DEBUG logging
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    request = InstallRequest(
        artifact_type=ArtifactType(args.artifact_type),
        name=args.artifact_name,
        targets=tuple(args.targets),
        scope=Scope(args.scope),
        mode=InstallMode.COPY if args.copy else InstallMode.SYMLINK,
        force=args.force,
        dry_run=args.dry_run,
        assume_yes=args.yes,
        no_cache=args.no_cache,
    )

    try:
        result = install_artifact(request)
    except UsageError as exc:
        if args.json_output:
            print(
                json.dumps(
                    {"success": False, "exitCode": exc.exit_code, "error": str(exc)}, indent=2
                )
            )
        else:
            print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except (AmbiguousTargetsError, NoTargetsFoundError) as exc:
        if args.json_output:
            print(
                json.dumps(
                    {"success": False, "exitCode": EXIT_AUTODETECT_FAILURE, "error": str(exc)},
                    indent=2,
                )
            )
        else:
            print(f"error: {exc}", file=sys.stderr)
        return EXIT_AUTODETECT_FAILURE
    except NetworkError as exc:
        if args.json_output:
            print(
                json.dumps(
                    {"success": False, "exitCode": EXIT_NETWORK_ERROR, "error": str(exc)}, indent=2
                )
            )
        else:
            print(f"error: {exc}", file=sys.stderr)
        return EXIT_NETWORK_ERROR
    except Exception as exc:
        # Import here to avoid circular dependency at module level
        from aidriven.install._archive import IntegrityError

        if isinstance(exc, IntegrityError):
            if args.json_output:
                print(
                    json.dumps(
                        {"success": False, "exitCode": EXIT_INTEGRITY_ERROR, "error": str(exc)},
                        indent=2,
                    )
                )
            else:
                print(f"error: integrity check failed — {exc}", file=sys.stderr)
            return EXIT_INTEGRITY_ERROR
        raise

    if args.json_output:
        print(_format_json(result))
    elif not args.quiet or not result.success:
        output = _format_human(result, use_color=use_color, verbose=args.verbose, quiet=args.quiet)
        if output:
            print(output)

    return result.exit_code
