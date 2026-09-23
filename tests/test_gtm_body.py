"""Core safety contracts for local GTM request-body intake."""

from __future__ import annotations

from pathlib import Path

import pytest

from gtmctl.foundation.body import MAX_JSON_BODY_BYTES, read_json_object
from gtmctl.foundation.validation import RequestValidationError


def test_json_body_intake_rejects_oversized_payload_before_parsing(
    tmp_path: Path,
) -> None:
    body = tmp_path / "oversized.json"
    body.write_bytes(b"{" + (b"x" * MAX_JSON_BODY_BYTES) + b"}")

    with pytest.raises(RequestValidationError, match="must not exceed"):
        read_json_object(str(body))
