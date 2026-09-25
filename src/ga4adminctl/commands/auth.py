"""Native OAuth commands for GA4 Admin access."""

from marketing_common.oauth_cli import make_auth_app

app = make_auth_app("ga4adminctl")
