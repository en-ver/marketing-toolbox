# SDK-backed CLI introspection

**Status:** current v1 behavior
**Applies to:** `ga4datactl`, `ga4adminctl`, and `gtmctl`

## Purpose

The `sdk schema` command exposes request fields and fixed enum values from the
installed official SDK or bundled official Discovery artifact. It helps a
caller construct an opaque `--body` without maintaining a second hand-written
Google schema catalog.

The command accepts only a registered body-bearing CLI leaf:

```text
<tool> sdk schema --command "<existing command path>"
```

It does not provide a generic Google API proxy, arbitrary SDK method runner,
URL/HTTP client, import path, or dynamic command generator.

## Data sources and boundaries

Static descriptor data is read locally. It includes source-provided message
fields, JSON names, scalar and message kinds, repeated fields, one-of groups,
references, fixed enum names and numbers, and documentation when available.
Static lookup does not load credentials, construct an API service, make a
network request, paginate, retry, or dispatch a Google operation.

| CLI | Local static source | Explicit live discovery |
| --- | --- | --- |
| `ga4datactl` | Pinned generated protobuf descriptors and enums | Existing read-only metadata and compatibility commands |
| `ga4adminctl` | Pinned generated protobuf descriptors and enums | Existing approved Admin reads |
| `gtmctl` | Bundled v2 Discovery document | Existing approved GTM reads |

Live values remain the responsibility of explicit read-only commands. Static
introspection does not claim a universal live metadata endpoint for APIs that
do not provide one. If the local GTM Discovery artifact is unavailable, the
command returns a structured diagnostic instead of fetching it.

## Interface and output

`--command` names an existing registered leaf, excluding the tool name. The
response uses the normal success envelope and identifies the CLI path, official
method, source artifact or package, version, and request descriptor. It
separates fields supplied by CLI path/query options from fields supplied in the
opaque body and fields forbidden in that body because the CLI supplies them.

The descriptor is an adapter over the installed official source; it does not
add a local validation gate that can diverge from Google. Unknown, partial,
group-only, excluded, and unregistered paths are invalid arguments and do not
perform credential or network activity.

For GTM Gallery import, the body describes the three official Discovery query
fields. The response identifies this as an official query-parameter envelope
and marks `parent` and the CLI-owned permission acknowledgement as
body-forbidden.

## Caller workflow

1. Use `<tool> --help` and descendant help to select an existing leaf.
2. Read the leaf help for path, query, and safety options.
3. Run `sdk schema` when the leaf accepts an opaque body and static fields or
   enums are needed.
4. Use explicit read-only commands for account- or property-specific values.
5. Construct the body and invoke the selected operation with its normal safety
   controls.

The command is intentionally one leaf at a time. It does not dump the entire
SDK or select fields, enum values, resources, or acknowledgements for the
caller.

## Contract requirements

Every successful response includes source provenance and values derived from
the pinned official artifact. Registered mappings must point to existing,
non-excluded body-bearing leaves. Existing command, authentication, mutation,
redaction, pagination, help, test, type, and packaging contracts continue to
apply.
