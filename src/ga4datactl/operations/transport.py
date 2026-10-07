"""GA4 Data credential and official-client transport."""

from __future__ import annotations

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.auth.credentials import Credentials

from marketing_common.auth import resolve_credentials
from marketing_common.oauth import scope_for_access


def credentials_for_access(access: str) -> Credentials:
    """Resolve credentials for one GA4 Data access tier."""
    return resolve_credentials(
        [scope_for_access("ga4datactl", access)], tool="ga4datactl"
    )


def make_client(credentials: Credentials) -> BetaAnalyticsDataClient:
    """Construct the official GA4 Data client with resolved credentials."""
    return BetaAnalyticsDataClient(credentials=credentials)
