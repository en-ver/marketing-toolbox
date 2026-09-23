"""Pinned compatibility boundary for Typer's vendored Click exceptions.

Typer 0.27.0 vendors Click under ``typer._click`` and does not expose these
parse exceptions from a public module. Keep that version-specific dependency
here so command execution remains insulated from a future Typer layout change.
"""

from typer._click.exceptions import NoArgsIsHelpError, UsageError

__all__ = ["NoArgsIsHelpError", "UsageError"]
