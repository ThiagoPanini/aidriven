"""aidriven CLI entry point."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        prog="aidriven",
        description="AI-driven developer tools CLI.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # Register 'install' subcommand
    subparsers.add_parser(
        "install",
        help="Install an artifact (e.g. a skill) from aidriven-resources.",
        add_help=False,
    )

    if argv is None:
        argv = sys.argv[1:]

    # Route install subcommand to its own module
    if argv and argv[0] == "install":
        from aidriven.cli._install_cmd import run_install_cmd

        return run_install_cmd(argv[1:])

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    return 0


def cli_entry() -> None:
    """Console-scripts entry point."""
    sys.exit(main())
