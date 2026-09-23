"""Validated GA4 Admin API adapters."""
# ruff: noqa: F401

from __future__ import annotations

import re

from google.analytics.admin_v1beta import (
    AnalyticsAdminServiceClient as V1BetaAnalyticsAdminServiceClient,
)
from google.analytics.admin_v1beta.types import (
    Account,
    AcknowledgeUserDataCollectionRequest,
    AcknowledgeUserDataCollectionResponse,
    ArchiveCustomDimensionRequest,
    ArchiveCustomMetricRequest,
    CreateCustomDimensionRequest,
    CreateCustomMetricRequest,
    CreateDataStreamRequest,
    CreateFirebaseLinkRequest,
    CreateGoogleAdsLinkRequest,
    CreateKeyEventRequest,
    CreateMeasurementProtocolSecretRequest,
    CreatePropertyRequest,
    CustomDimension,
    CustomMetric,
    DataRetentionSettings,
    DataSharingSettings,
    DataStream,
    DeleteAccountRequest,
    DeleteDataStreamRequest,
    DeleteFirebaseLinkRequest,
    DeleteGoogleAdsLinkRequest,
    DeleteKeyEventRequest,
    DeleteMeasurementProtocolSecretRequest,
    DeletePropertyRequest,
    FirebaseLink,
    GetAccountRequest,
    GetCustomDimensionRequest,
    GetCustomMetricRequest,
    GetDataRetentionSettingsRequest,
    GetDataSharingSettingsRequest,
    GetDataStreamRequest,
    GetKeyEventRequest,
    GetMeasurementProtocolSecretRequest,
    GetPropertyRequest,
    GoogleAdsLink,
    KeyEvent,
    ListAccountsRequest,
    ListAccountsResponse,
    ListAccountSummariesRequest,
    ListAccountSummariesResponse,
    ListCustomDimensionsRequest,
    ListCustomDimensionsResponse,
    ListCustomMetricsRequest,
    ListCustomMetricsResponse,
    ListDataStreamsRequest,
    ListDataStreamsResponse,
    ListFirebaseLinksRequest,
    ListFirebaseLinksResponse,
    ListGoogleAdsLinksRequest,
    ListGoogleAdsLinksResponse,
    ListKeyEventsRequest,
    ListKeyEventsResponse,
    ListMeasurementProtocolSecretsRequest,
    ListMeasurementProtocolSecretsResponse,
    ListPropertiesRequest,
    ListPropertiesResponse,
    MeasurementProtocolSecret,
    Property,
    ProvisionAccountTicketRequest,
    ProvisionAccountTicketResponse,
    RunAccessReportRequest,
    RunAccessReportResponse,
    SearchChangeHistoryEventsRequest,
    SearchChangeHistoryEventsResponse,
    UpdateAccountRequest,
    UpdateCustomDimensionRequest,
    UpdateCustomMetricRequest,
    UpdateDataRetentionSettingsRequest,
    UpdateDataStreamRequest,
    UpdateGoogleAdsLinkRequest,
    UpdateKeyEventRequest,
    UpdateMeasurementProtocolSecretRequest,
    UpdatePropertyRequest,
)
from google.api_core import exceptions
from google.oauth2.service_account import Credentials

from ga4adminctl.foundation.errors import GoogleApiError as _GoogleApiError
from ga4adminctl.foundation.errors import normalize_google_error
from ga4adminctl.foundation.serialization import (
    message_response,
    raw_message_response,
    remove_secret_values,
    secret_metadata_response,
)
from ga4adminctl.foundation.validation import (
    ACCOUNT_PATTERN as _ACCOUNT_PATTERN,
)
from ga4adminctl.foundation.validation import (
    DATA_RETENTION_SETTINGS_PATTERN,
    DATA_SHARING_SETTINGS_PATTERN,
    DATA_STREAM_PATTERN,
    FIREBASE_LINK_PATTERN,
    GOOGLE_ADS_LINK_PATTERN,
    KEY_EVENT_PATTERN,
    MAX_BODY_CHARACTERS,
    MAX_PROPERTY_PAGE_SIZE,
    MEASUREMENT_PROTOCOL_SECRET_PATTERN,
    parse_sdk_message,
    read_json_body,
    reject_route_fields,
    validate_page_request,
    validate_properties_list_request,
    validate_property_name,
    validate_resource_name,
)
from ga4adminctl.foundation.validation import (
    PROPERTY_LIST_FILTER_PATTERN as _PROPERTY_LIST_FILTER_PATTERN,
)
from ga4adminctl.foundation.validation import (
    PROPERTY_PATTERN as _PROPERTY_PATTERN,
)
from ga4adminctl.foundation.validation import (
    RequestValidationError as _RequestValidationError,
)
from ga4adminctl.operations import access as _access
from ga4adminctl.operations import accounts as _accounts
from ga4adminctl.operations import mutations as _mutations
from ga4adminctl.operations import properties as _properties
from ga4adminctl.operations import reads as _reads
from ga4adminctl.operations import resources as _resources
from ga4adminctl.operations import secrets as _secrets
from marketing_common.auth import (
    CredentialConfigurationError,
    service_account_credentials,
)

# These names remain explicit compatibility exports.
__all__ = [
    "MAX_BODY_CHARACTERS",
    "CredentialConfigurationError",
    "GoogleApiError",
    "RequestValidationError",
]

# Static aliases preserve the legacy service import surface.
delete_account = _accounts.delete_account
get_account = _accounts.get_account
list_account_summaries = _accounts.list_account_summaries
list_accounts = _accounts.list_accounts
update_account = _accounts.update_account
provision_account_ticket = _accounts.provision_account_ticket
create_property = _properties.create_property
delete_property = _properties.delete_property
get_data_retention_settings = _properties.get_data_retention_settings
get_data_sharing_settings = _properties.get_data_sharing_settings
get_property = _properties.get_property
list_properties = _properties.list_properties
update_data_retention_settings = _properties.update_data_retention_settings
update_property = _properties.update_property
acknowledge_user_data_collection = _properties.acknowledge_user_data_collection
archive_custom_dimension = _resources.archive_custom_dimension
archive_custom_metric = _resources.archive_custom_metric
create_custom_dimension = _resources.create_custom_dimension
create_custom_metric = _resources.create_custom_metric
create_data_stream = _resources.create_data_stream
create_firebase_link = _resources.create_firebase_link
create_google_ads_link = _resources.create_google_ads_link
create_key_event = _resources.create_key_event
delete_data_stream = _resources.delete_data_stream
delete_firebase_link = _resources.delete_firebase_link
delete_google_ads_link = _resources.delete_google_ads_link
delete_key_event = _resources.delete_key_event
run_access_report = _access.run_access_report
search_change_history_events = _access.search_change_history_events
get_measurement_protocol_secret = _secrets.get_measurement_protocol_secret
list_measurement_protocol_secrets = _secrets.list_measurement_protocol_secrets
create_measurement_protocol_secret = _secrets.create_measurement_protocol_secret
update_measurement_protocol_secret = _secrets.update_measurement_protocol_secret
delete_measurement_protocol_secret = _secrets.delete_measurement_protocol_secret
get_custom_dimension = _resources.get_custom_dimension
get_custom_metric = _resources.get_custom_metric
get_data_stream = _resources.get_data_stream
get_key_event = _resources.get_key_event
list_custom_dimensions = _resources.list_custom_dimensions
list_custom_metrics = _resources.list_custom_metrics
list_data_streams = _resources.list_data_streams
list_firebase_links = _resources.list_firebase_links
list_google_ads_links = _resources.list_google_ads_links
list_key_events = _resources.list_key_events
update_custom_dimension = _resources.update_custom_dimension
update_custom_metric = _resources.update_custom_metric
update_data_stream = _resources.update_data_stream
update_google_ads_link = _resources.update_google_ads_link
update_key_event = _resources.update_key_event
_child_patterns = _resources._child_patterns
_get_child = _resources._get_child
_list_child = _resources._list_child
_update_child = _resources._update_child
PropertiesClient = _reads.PropertiesClient
PropertiesClientFactory = _reads.PropertiesClientFactory
_list_v1beta = _reads._list_v1beta
_make_properties_client = _reads._make_properties_client
_read_v1beta = _reads._read_v1beta
_write_v1beta = _mutations._write_v1beta

ANALYTICS_EDIT_SCOPE = "https://www.googleapis.com/auth/analytics.edit"
ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
PROPERTY_READ_TIMEOUT_SECONDS = 20.0

# Foundation compatibility re-exports retained by this facade.
GoogleApiError = _GoogleApiError
RequestValidationError = _RequestValidationError
ACCOUNT_PATTERN = _ACCOUNT_PATTERN
PROPERTY_LIST_FILTER_PATTERN = _PROPERTY_LIST_FILTER_PATTERN
PROPERTY_PATTERN = _PROPERTY_PATTERN
_normalize_google_error = normalize_google_error
_message_response = message_response
_raw_message_response = raw_message_response
_remove_secret_values = remove_secret_values
_secret_metadata_response = secret_metadata_response
