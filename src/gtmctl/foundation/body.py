"""Bounded, local JSON request-body intake for GTM mutations."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from gtmctl.foundation.validation import RequestValidationError

MAX_JSON_BODY_BYTES = 1_048_576


def _reject_nonfinite_json_constant(_constant: str) -> Any:
    raise ValueError


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError
    return parsed


def read_json_object(source: str) -> dict[str, Any]:
    """Read one bounded UTF-8 JSON object from a file or standard input."""
    if source == "-":
        raw = sys.stdin.buffer.read(MAX_JSON_BODY_BYTES + 1)
    else:
        try:
            with Path(source).open("rb") as body_file:
                raw = body_file.read(MAX_JSON_BODY_BYTES + 1)
        except OSError as exc:
            raise RequestValidationError(
                f"--body could not be read: {exc.strerror}."
            ) from exc

    if len(raw) > MAX_JSON_BODY_BYTES:
        raise RequestValidationError(
            f"--body must not exceed {MAX_JSON_BODY_BYTES} bytes."
        )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RequestValidationError("--body must be valid UTF-8 JSON.") from exc
    try:
        value = json.loads(
            decoded,
            parse_constant=_reject_nonfinite_json_constant,
            parse_float=_parse_finite_json_float,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise RequestValidationError("--body must contain valid JSON.") from exc
    if not isinstance(value, dict):
        raise RequestValidationError("--body must contain a JSON object.")
    return value


def body_sha256(body: dict[str, Any]) -> str:
    """Return a deterministic, non-reversible payload identifier for dry runs."""
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
