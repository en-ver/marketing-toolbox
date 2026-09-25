"""Native OAuth commands for GA4 Data access."""

from marketing_common.oauth_cli import make_auth_app

app = make_auth_app("ga4datactl")
