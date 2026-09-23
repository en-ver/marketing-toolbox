"""GA4 Data response serialization helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, cast

from google.protobuf.json_format import (
    MessageToDict,
    ParseDict,
    ParseError,
)

from ga4datactl.foundation.validation import RequestValidationError


class ProtoPlusResponse(Protocol):
    """The proto-plus surface needed for official JSON serialization."""


def parse_request(request: Mapping[str, Any], target: Any) -> None:
    """Populate an official protobuf request from the public JSON contract."""
    try:
        ParseDict(dict(request), type(target).pb(target))
    except (ParseError, ValueError, RecursionError) as exc:
        raise RequestValidationError(
            "--body cannot be converted to a GA4 request."
        ) from exc


def response_to_json(response: ProtoPlusResponse) -> dict[str, Any]:
    """Preserve a proto-plus response using official protobuf JSON field names."""
    proto_plus_response = cast(Any, response)
    return dict(
        MessageToDict(
            type(proto_plus_response).pb(proto_plus_response),
            preserving_proto_field_name=False,
            use_integers_for_enums=False,
        )
    )
