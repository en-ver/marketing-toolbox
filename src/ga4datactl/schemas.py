"""Bundled JSON Schemas for versioned GA4 Data API request contracts."""

from __future__ import annotations

import json
from typing import Any

CORE_REPORTING_DEFINITIONS: dict[str, Any] = json.loads(
    '{"$defs": {"BatchRunReportsRequest": {"additionalProperties": false, "description": "The batch request containing multiple report requests.", "id": "BatchRunReportsRequest", "properties": {"requests": {"description": "Individual requests. Each request has a separate report response. Each batch request is allowed up to 5 requests.", "items": {"$ref": "#/$defs/RunReportRequest"}, "maxItems": 5, "minItems": 1, "type": "array"}}, "type": "object"}, "BetweenFilter": {"additionalProperties": false, "description": "To express that the result needs to be between two numbers (inclusive).", "id": "BetweenFilter", "properties": {"fromValue": {"$ref": "#/$defs/NumericValue"}, "toValue": {"$ref": "#/$defs/NumericValue"}}, "type": "object"}, "CaseExpression": {"additionalProperties": false, "description": "Used to convert a dimension value to a single case.", "id": "CaseExpression", "properties": {"dimensionName": {"description": "Name of a dimension. The name must refer back to a name in dimensions field of the request.", "type": "string"}}, "type": "object"}, "Cohort": {"additionalProperties": false, "description": "Defines a cohort selection criteria. A cohort is a group of users who share a common characteristic. For example, users with the same `firstSessionDate` belong to the same cohort.", "id": "Cohort", "properties": {"dateRange": {"$ref": "#/$defs/DateRange"}, "dimension": {"description": "Dimension used by the cohort. Required and only supports `firstSessionDate`.", "type": "string"}, "name": {"description": "Assigns a name to this cohort. The dimension `cohort` is valued to this name in a report response. If set, cannot begin with `cohort_` or `RESERVED_`. If not set, cohorts are named by their zero based index `cohort_0`, `cohort_1`, etc.", "type": "string"}}, "type": "object"}, "CohortReportSettings": {"additionalProperties": false, "description": "Optional settings of a cohort report.", "id": "CohortReportSettings", "properties": {"accumulate": {"description": "If true, accumulates the result from first touch day to the end day. Not supported in `RunReportRequest`.", "type": "boolean"}}, "type": "object"}, "CohortSpec": {"additionalProperties": false, "description": "The specification of cohorts for a cohort report. Cohort reports create a time series of user retention for the cohort. For example, you could select the cohort of users that were acquired in the first week of September and follow that cohort for the next six weeks. Selecting the users acquired in the first week of September cohort is specified in the `cohort` object. Following that cohort for the next six weeks is specified in the `cohortsRange` object. For examples, see [Cohort Report Examples](https://developers.google.com/analytics/devguides/reporting/data/v1/advanced#cohort_report_examples). The report response could show a weekly time series where say your app has retained 60% of this cohort after three weeks and 25% of this cohort after six weeks. These two percentages can be calculated by the metric `cohortActiveUsers/cohortTotalUsers` and will be separate rows in the report.", "id": "CohortSpec", "properties": {"cohortReportSettings": {"$ref": "#/$defs/CohortReportSettings"}, "cohorts": {"description": "Defines the selection criteria to group users into cohorts. Most cohort reports define only a single cohort. If multiple cohorts are specified, each cohort can be recognized in the report by their name.", "items": {"$ref": "#/$defs/Cohort"}, "type": "array"}, "cohortsRange": {"$ref": "#/$defs/CohortsRange"}}, "type": "object"}, "CohortsRange": {"additionalProperties": false, "description": "Configures the extended reporting date range for a cohort report. Specifies an offset duration to follow the cohorts over.", "id": "CohortsRange", "properties": {"endOffset": {"description": "Required. `endOffset` specifies the end date of the extended reporting date range for a cohort report. `endOffset` can be any positive integer but is commonly set to 5 to 10 so that reports contain data on the cohort for the next several granularity time periods. If `granularity` is `DAILY`, the `endDate` of the extended reporting date range is `endDate` of the cohort plus `endOffset` days. If `granularity` is `WEEKLY`, the `endDate` of the extended reporting date range is `endDate` of the cohort plus `endOffset * 7` days. If `granularity` is `MONTHLY`, the `endDate` of the extended reporting date range is `endDate` of the cohort plus `endOffset * 30` days.", "format": "int32", "type": "integer"}, "granularity": {"description": "Required. The granularity used to interpret the `startOffset` and `endOffset` for the extended reporting date range for a cohort report.", "enum": ["GRANULARITY_UNSPECIFIED", "DAILY", "WEEKLY", "MONTHLY"], "enumDescriptions": ["Should never be specified.", "Daily granularity. Commonly used if the cohort\'s `dateRange` is a single day and the request contains `cohortNthDay`.", "Weekly granularity. Commonly used if the cohort\'s `dateRange` is a week in duration (starting on Sunday and ending on Saturday) and the request contains `cohortNthWeek`.", "Monthly granularity. Commonly used if the cohort\'s `dateRange` is a month in duration and the request contains `cohortNthMonth`."], "type": "string"}, "startOffset": {"description": "`startOffset` specifies the start date of the extended reporting date range for a cohort report. `startOffset` is commonly set to 0 so that reports contain data from the acquisition of the cohort forward. If `granularity` is `DAILY`, the `startDate` of the extended reporting date range is `startDate` of the cohort plus `startOffset` days. If `granularity` is `WEEKLY`, the `startDate` of the extended reporting date range is `startDate` of the cohort plus `startOffset * 7` days. If `granularity` is `MONTHLY`, the `startDate` of the extended reporting date range is `startDate` of the cohort plus `startOffset * 30` days.", "format": "int32", "type": "integer"}}, "type": "object"}, "Comparison": {"additionalProperties": false, "description": "Defines an individual comparison. Most requests will include multiple comparisons so that the report compares between the comparisons.", "id": "Comparison", "properties": {"comparison": {"description": "A saved comparison identified by the comparison\'s resource name. For example, \'comparisons/1234\'.", "type": "string"}, "dimensionFilter": {"$ref": "#/$defs/FilterExpression"}, "name": {"description": "Each comparison produces separate rows in the response. In the response, this comparison is identified by this name. If name is unspecified, we will use the saved comparisons display name.", "type": "string"}}, "type": "object"}, "ConcatenateExpression": {"additionalProperties": false, "description": "Used to combine dimension values to a single dimension.", "id": "ConcatenateExpression", "properties": {"delimiter": {"description": "The delimiter placed between dimension names. Delimiters are often single characters such as \\"|\\" or \\",\\" but can be longer strings. If a dimension value contains the delimiter, both will be present in response with no distinction. For example if dimension 1 value = \\"US,FR\\", dimension 2 value = \\"JP\\", and delimiter = \\",\\", then the response will contain \\"US,FR,JP\\".", "type": "string"}, "dimensionNames": {"description": "Names of dimensions. The names must refer back to names in the dimensions field of the request.", "items": {"type": "string"}, "type": "array"}}, "type": "object"}, "DateRange": {"additionalProperties": false, "description": "A contiguous set of days: `startDate`, `startDate + 1`, ..., `endDate`. Requests are allowed up to 4 date ranges.", "id": "DateRange", "properties": {"endDate": {"description": "The inclusive end date for the query in the format `YYYY-MM-DD`. Cannot be before `start_date`. The format `NdaysAgo`, `yesterday`, or `today` is also accepted, and in that case, the date is inferred based on the property\'s reporting time zone.", "type": "string"}, "name": {"description": "Assigns a name to this date range. The dimension `dateRange` is valued to this name in a report response. If set, cannot begin with `date_range_` or `RESERVED_`. If not set, date ranges are named by their zero based index in the request: `date_range_0`, `date_range_1`, etc.", "type": "string"}, "startDate": {"description": "The inclusive start date for the query in the format `YYYY-MM-DD`. Cannot be after `end_date`. The format `NdaysAgo`, `yesterday`, or `today` is also accepted, and in that case, the date is inferred based on the property\'s reporting time zone.", "type": "string"}}, "type": "object"}, "Dimension": {"additionalProperties": false, "description": "Dimensions are attributes of your data. For example, the dimension city indicates the city from which an event originates. Dimension values in report responses are strings; for example, the city could be \\"Paris\\" or \\"New York\\". Requests are allowed up to 9 dimensions.", "id": "Dimension", "properties": {"dimensionExpression": {"$ref": "#/$defs/DimensionExpression"}, "name": {"description": "The name of the dimension. See the [API Dimensions](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#dimensions) for the list of dimension names supported by core reporting methods such as `runReport` and `batchRunReports`. See [Realtime Dimensions](https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#dimensions) for the list of dimension names supported by the `runRealtimeReport` method. See [Funnel Dimensions](https://developers.google.com/analytics/devguides/reporting/data/v1/exploration-api-schema#dimensions) for the list of dimension names supported by the `runFunnelReport` method. If `dimensionExpression` is specified, `name` can be any string that you would like within the allowed character set. For example if a `dimensionExpression` concatenates `country` and `city`, you could call that dimension `countryAndCity`. Dimension names that you choose must match the regular expression `^[a-zA-Z0-9_]$`. Dimensions are referenced by `name` in `dimensionFilter`, `orderBys`, `dimensionExpression`, and `pivots`.", "type": "string"}}, "type": "object"}, "DimensionExpression": {"additionalProperties": false, "description": "Used to express a dimension which is the result of a formula of multiple dimensions. Example usages: 1) lower_case(dimension) 2) concatenate(dimension1, symbol, dimension2).", "id": "DimensionExpression", "properties": {"concatenate": {"$ref": "#/$defs/ConcatenateExpression"}, "lowerCase": {"$ref": "#/$defs/CaseExpression"}, "upperCase": {"$ref": "#/$defs/CaseExpression"}}, "type": "object"}, "DimensionOrderBy": {"additionalProperties": false, "description": "Sorts by dimension values.", "id": "DimensionOrderBy", "properties": {"dimensionName": {"description": "A dimension name in the request to order by.", "type": "string"}, "orderType": {"description": "Controls the rule for dimension value ordering.", "enum": ["ORDER_TYPE_UNSPECIFIED", "ALPHANUMERIC", "CASE_INSENSITIVE_ALPHANUMERIC", "NUMERIC"], "enumDescriptions": ["Unspecified.", "Alphanumeric sort by Unicode code point. For example, \\"2\\" < \\"A\\" < \\"X\\" < \\"b\\" < \\"z\\".", "Case insensitive alphanumeric sort by lower case Unicode code point. For example, \\"2\\" < \\"A\\" < \\"b\\" < \\"X\\" < \\"z\\".", "Dimension values are converted to numbers before sorting. For example in NUMERIC sort, \\"25\\" < \\"100\\", and in `ALPHANUMERIC` sort, \\"100\\" < \\"25\\". Non-numeric dimension values all have equal ordering value below all numeric values."], "type": "string"}}, "type": "object"}, "EmptyFilter": {"additionalProperties": false, "description": "Filter for empty values.", "id": "EmptyFilter", "properties": {}, "type": "object"}, "Filter": {"additionalProperties": false, "description": "An expression to filter dimension or metric values.", "id": "Filter", "properties": {"betweenFilter": {"$ref": "#/$defs/BetweenFilter"}, "emptyFilter": {"$ref": "#/$defs/EmptyFilter"}, "fieldName": {"description": "The dimension name or metric name. In most methods, dimensions & metrics can be used for the first time in this field. However in a RunPivotReportRequest, this field must be additionally specified by name in the RunPivotReportRequest\'s dimensions or metrics.", "type": "string"}, "inListFilter": {"$ref": "#/$defs/InListFilter"}, "numericFilter": {"$ref": "#/$defs/NumericFilter"}, "stringFilter": {"$ref": "#/$defs/StringFilter"}}, "type": "object"}, "FilterExpression": {"additionalProperties": false, "description": "To express dimension or metric filters. The fields in the same FilterExpression need to be either all dimensions or all metrics.", "id": "FilterExpression", "properties": {"andGroup": {"$ref": "#/$defs/FilterExpressionList"}, "filter": {"$ref": "#/$defs/Filter"}, "notExpression": {"$ref": "#/$defs/FilterExpression"}, "orGroup": {"$ref": "#/$defs/FilterExpressionList"}}, "type": "object"}, "FilterExpressionList": {"additionalProperties": false, "description": "A list of filter expressions.", "id": "FilterExpressionList", "properties": {"expressions": {"description": "A list of filter expressions.", "items": {"$ref": "#/$defs/FilterExpression"}, "type": "array"}}, "type": "object"}, "InListFilter": {"additionalProperties": false, "description": "The result needs to be in a list of string values.", "id": "InListFilter", "properties": {"caseSensitive": {"description": "If true, the string value is case sensitive.", "type": "boolean"}, "values": {"description": "The list of string values. Must be non-empty.", "items": {"type": "string"}, "type": "array"}}, "type": "object"}, "Metric": {"additionalProperties": false, "description": "The quantitative measurements of a report. For example, the metric `eventCount` is the total number of events. Requests are allowed up to 10 metrics.", "id": "Metric", "properties": {"expression": {"description": "A mathematical expression for derived metrics. For example, the metric Event count per user is `eventCount/totalUsers`.", "type": "string"}, "invisible": {"description": "Indicates if a metric is invisible in the report response. If a metric is invisible, the metric will not produce a column in the response, but can be used in `metricFilter`, `orderBys`, or a metric `expression`.", "type": "boolean"}, "name": {"description": "The name of the metric. See the [API Metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#metrics) for the list of metric names supported by core reporting methods such as `runReport` and `batchRunReports`. See [Realtime Metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#metrics) for the list of metric names supported by the `runRealtimeReport` method. See [Funnel Metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/exploration-api-schema#metrics) for the list of metric names supported by the `runFunnelReport` method. If `expression` is specified, `name` can be any string that you would like within the allowed character set. For example if `expression` is `screenPageViews/sessions`, you could call that metric\'s name = `viewsPerSession`. Metric names that you choose must match the regular expression `^[a-zA-Z0-9_]$`. Metrics are referenced by `name` in `metricFilter`, `orderBys`, and metric `expression`.", "type": "string"}}, "type": "object"}, "MetricOrderBy": {"additionalProperties": false, "description": "Sorts by metric values.", "id": "MetricOrderBy", "properties": {"metricName": {"description": "A metric name in the request to order by.", "type": "string"}}, "type": "object"}, "NumericFilter": {"additionalProperties": false, "description": "Filters for numeric or date values.", "id": "NumericFilter", "properties": {"operation": {"description": "The operation type for this filter.", "enum": ["OPERATION_UNSPECIFIED", "EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL", "GREATER_THAN", "GREATER_THAN_OR_EQUAL"], "enumDescriptions": ["Unspecified.", "Equal", "Less than", "Less than or equal", "Greater than", "Greater than or equal"], "type": "string"}, "value": {"$ref": "#/$defs/NumericValue"}}, "type": "object"}, "NumericValue": {"additionalProperties": false, "description": "To represent a number.", "id": "NumericValue", "properties": {"doubleValue": {"description": "Double value", "format": "double", "type": "number"}, "int64Value": {"description": "Integer value", "format": "int64", "type": "string"}}, "type": "object"}, "OrderBy": {"additionalProperties": false, "description": "Order bys define how rows will be sorted in the response. For example, ordering rows by descending event count is one ordering, and ordering rows by the event name string is a different ordering.", "id": "OrderBy", "properties": {"desc": {"description": "If true, sorts by descending order.", "type": "boolean"}, "dimension": {"$ref": "#/$defs/DimensionOrderBy"}, "metric": {"$ref": "#/$defs/MetricOrderBy"}, "pivot": {"$ref": "#/$defs/PivotOrderBy"}}, "type": "object"}, "Pivot": {"additionalProperties": false, "description": "Describes the visible dimension columns and rows in the report response.", "id": "Pivot", "properties": {"fieldNames": {"description": "Dimension names for visible columns in the report response. Including \\"dateRange\\" produces a date range column; for each row in the response, dimension values in the date range column will indicate the corresponding date range from the request.", "items": {"type": "string"}, "type": "array"}, "limit": {"description": "The number of unique combinations of dimension values to return in this pivot. The `limit` parameter is required. A `limit` of 10,000 is common for single pivot requests. The product of the `limit` for each `pivot` in a `RunPivotReportRequest` must not exceed 250,000. For example, a two pivot request with `limit: 1000` in each pivot will fail because the product is `1,000,000`.", "format": "int64", "pattern": "^[1-9][0-9]*$", "type": "string"}, "metricAggregations": {"description": "Aggregate the metrics by dimensions in this pivot using the specified metric_aggregations.", "items": {"enum": ["METRIC_AGGREGATION_UNSPECIFIED", "TOTAL", "MINIMUM", "MAXIMUM", "COUNT"], "enumDescriptions": ["Unspecified operator.", "SUM operator.", "Minimum operator.", "Maximum operator.", "Count operator."], "type": "string"}, "type": "array"}, "offset": {"description": "The row count of the start row. The first row is counted as row 0.", "format": "int64", "type": "string"}, "orderBys": {"description": "Specifies how dimensions are ordered in the pivot. In the first Pivot, the OrderBys determine Row and PivotDimensionHeader ordering; in subsequent Pivots, the OrderBys determine only PivotDimensionHeader ordering. Dimensions specified in these OrderBys must be a subset of Pivot.field_names.", "items": {"$ref": "#/$defs/OrderBy"}, "type": "array"}}, "required": ["limit"], "type": "object"}, "PivotOrderBy": {"additionalProperties": false, "description": "Sorts by a pivot column group.", "id": "PivotOrderBy", "properties": {"metricName": {"description": "In the response to order by, order rows by this column. Must be a metric name from the request.", "type": "string"}, "pivotSelections": {"description": "Used to select a dimension name and value pivot. If multiple pivot selections are given, the sort occurs on rows where all pivot selection dimension name and value pairs match the row\'s dimension name and value pair.", "items": {"$ref": "#/$defs/PivotSelection"}, "type": "array"}}, "type": "object"}, "PivotSelection": {"additionalProperties": false, "description": "A pair of dimension names and values. Rows with this dimension pivot pair are ordered by the metric\'s value. For example if pivots = {{\\"browser\\", \\"Chrome\\"}} and metric_name = \\"Sessions\\", then the rows will be sorted based on Sessions in Chrome. ---------|----------|----------------|----------|---------------- | Chrome | Chrome | Safari | Safari ---------|----------|----------------|----------|---------------- Country | Sessions | Pages/Sessions | Sessions | Pages/Sessions ---------|----------|----------------|----------|---------------- US | 2 | 2 | 3 | 1 ---------|----------|----------------|----------|---------------- Canada | 3 | 1 | 4 | 1 ---------|----------|----------------|----------|----------------", "id": "PivotSelection", "properties": {"dimensionName": {"description": "Must be a dimension name from the request.", "type": "string"}, "dimensionValue": {"description": "Order by only when the named dimension is this value.", "type": "string"}}, "type": "object"}, "RunPivotReportRequest": {"additionalProperties": false, "description": "The request to generate a pivot report.", "id": "RunPivotReportRequest", "properties": {"cohortSpec": {"$ref": "#/$defs/CohortSpec"}, "comparisons": {"description": "Optional. The configuration of comparisons requested and displayed. The request requires both a comparisons field and a comparisons dimension to receive a comparison column in the response.", "items": {"$ref": "#/$defs/Comparison"}, "type": "array"}, "currencyCode": {"description": "A currency code in ISO4217 format, such as \\"AED\\", \\"USD\\", \\"JPY\\". If the field is empty, the report uses the property\'s default currency.", "type": "string"}, "dateRanges": {"description": "The date range to retrieve event data for the report. If multiple date ranges are specified, event data from each date range is used in the report. A special dimension with field name \\"dateRange\\" can be included in a Pivot\'s field names; if included, the report compares between date ranges. In a cohort request, this `dateRanges` must be unspecified.", "items": {"$ref": "#/$defs/DateRange"}, "type": "array"}, "dimensionFilter": {"$ref": "#/$defs/FilterExpression"}, "dimensions": {"description": "The dimensions requested. All defined dimensions must be used by one of the following: dimension_expression, dimension_filter, pivots, order_bys.", "items": {"$ref": "#/$defs/Dimension"}, "type": "array"}, "keepEmptyRows": {"description": "If false or unspecified, each row with all metrics equal to 0 will not be returned. If true, these rows will be returned if they are not separately removed by a filter. Regardless of this `keep_empty_rows` setting, only data recorded by the Google Analytics property can be displayed in a report. For example if a property never logs a `purchase` event, then a query for the `eventName` dimension and `eventCount` metric will not have a row eventName: \\"purchase\\" and eventCount: 0.", "type": "boolean"}, "metricFilter": {"$ref": "#/$defs/FilterExpression"}, "metrics": {"description": "The metrics requested, at least one metric needs to be specified. All defined metrics must be used by one of the following: metric_expression, metric_filter, order_bys.", "items": {"$ref": "#/$defs/Metric"}, "maxItems": 10, "minItems": 1, "type": "array"}, "pivots": {"description": "Describes the visual format of the report\'s dimensions in columns or rows. The union of the fieldNames (dimension names) in all pivots must be a subset of dimension names defined in Dimensions. No two pivots can share a dimension. A dimension is only visible if it appears in a pivot.", "items": {"$ref": "#/$defs/Pivot"}, "minItems": 1, "type": "array"}, "returnPropertyQuota": {"description": "Toggles whether to return the current state of this Google Analytics property\'s quota. Quota is returned in [PropertyQuota](#PropertyQuota).", "type": "boolean"}}, "required": ["metrics", "pivots"], "type": "object"}, "RunReportRequest": {"additionalProperties": false, "description": "The request to generate a report.", "id": "RunReportRequest", "properties": {"cohortSpec": {"$ref": "#/$defs/CohortSpec"}, "comparisons": {"description": "Optional. The configuration of comparisons requested and displayed. The request only requires a comparisons field in order to receive a comparison column in the response.", "items": {"$ref": "#/$defs/Comparison"}, "type": "array"}, "currencyCode": {"description": "A currency code in ISO4217 format, such as \\"AED\\", \\"USD\\", \\"JPY\\". If the field is empty, the report uses the property\'s default currency.", "type": "string"}, "dateRanges": {"description": "Date ranges of data to read. If multiple date ranges are requested, each response row will contain a zero based date range index. If two date ranges overlap, the event data for the overlapping days is included in the response rows for both date ranges. In a cohort request, this `dateRanges` must be unspecified.", "items": {"$ref": "#/$defs/DateRange"}, "type": "array"}, "dimensionFilter": {"$ref": "#/$defs/FilterExpression"}, "dimensions": {"description": "The dimensions requested and displayed.", "items": {"$ref": "#/$defs/Dimension"}, "type": "array"}, "keepEmptyRows": {"description": "If false or unspecified, each row with all metrics equal to 0 will not be returned. If true, these rows will be returned if they are not separately removed by a filter. Regardless of this `keep_empty_rows` setting, only data recorded by the Google Analytics property can be displayed in a report. For example if a property never logs a `purchase` event, then a query for the `eventName` dimension and `eventCount` metric will not have a row eventName: \\"purchase\\" and eventCount: 0.", "type": "boolean"}, "limit": {"description": "The number of rows to return. If unspecified, 10,000 rows are returned. The API returns a maximum of 250,000 rows per request, no matter how many you ask for. `limit` must be positive. The API can also return fewer rows than the requested `limit`, if there aren\'t as many dimension values as the `limit`. For instance, there are fewer than 300 possible values for the dimension `country`, so when reporting on only `country`, you can\'t get more than 300 rows, even if you set `limit` to a higher value. To learn more about this pagination parameter, see [Pagination](https://developers.google.com/analytics/devguides/reporting/data/v1/basics#pagination).", "format": "int64", "type": "string"}, "metricAggregations": {"description": "Aggregation of metrics. Aggregated metric values will be shown in rows where the dimension_values are set to \\"RESERVED_(MetricAggregation)\\". Aggregates including both comparisons and multiple date ranges will be aggregated based on the date ranges.", "items": {"enum": ["METRIC_AGGREGATION_UNSPECIFIED", "TOTAL", "MINIMUM", "MAXIMUM", "COUNT"], "enumDescriptions": ["Unspecified operator.", "SUM operator.", "Minimum operator.", "Maximum operator.", "Count operator."], "type": "string"}, "type": "array"}, "metricFilter": {"$ref": "#/$defs/FilterExpression"}, "metrics": {"description": "The metrics requested and displayed.", "items": {"$ref": "#/$defs/Metric"}, "type": "array"}, "offset": {"description": "The row count of the start row. The first row is counted as row 0. When paging, the first request does not specify offset; or equivalently, sets offset to 0; the first request returns the first `limit` of rows. The second request sets offset to the `limit` of the first request; the second request returns the second `limit` of rows. To learn more about this pagination parameter, see [Pagination](https://developers.google.com/analytics/devguides/reporting/data/v1/basics#pagination).", "format": "int64", "type": "string"}, "orderBys": {"description": "Specifies how rows are ordered in the response. Requests including both comparisons and multiple date ranges will have order bys applied on the comparisons.", "items": {"$ref": "#/$defs/OrderBy"}, "type": "array"}, "returnPropertyQuota": {"description": "Toggles whether to return the current state of this Google Analytics property\'s quota. Quota is returned in [PropertyQuota](#PropertyQuota).", "type": "boolean"}}, "type": "object"}, "StringFilter": {"additionalProperties": false, "description": "The filter for string", "id": "StringFilter", "properties": {"caseSensitive": {"description": "If true, the string value is case sensitive.", "type": "boolean"}, "matchType": {"description": "The match type for this filter.", "enum": ["MATCH_TYPE_UNSPECIFIED", "EXACT", "BEGINS_WITH", "ENDS_WITH", "CONTAINS", "FULL_REGEXP", "PARTIAL_REGEXP"], "enumDescriptions": ["Unspecified", "Exact match of the string value.", "Begins with the string value.", "Ends with the string value.", "Contains the string value.", "Full match for the regular expression with the string value.", "Partial match for the regular expression with the string value."], "type": "string"}, "value": {"description": "The string value used for the matching.", "type": "string"}}, "type": "object"}}, "$id": "urn:marketing-tools:ga4datactl:schema:core-reporting-definitions.schema.json", "$schema": "https://json-schema.org/draft/2020-12/schema", "description": "Shared structural definitions transcribed from the official Google Discovery document (20260722).", "title": "GA4 Data API v1beta core reporting definitions", "x-google-discovery-revision": "20260722", "x-google-discovery-url": "https://analyticsdata.googleapis.com/$discovery/rest?version=v1beta"}'
)


def _operation_schema(definition: str, *, schema_id: str, title: str) -> dict[str, Any]:
    return {
        **CORE_REPORTING_DEFINITIONS,
        "$id": schema_id,
        "title": title,
        "$ref": f"#/$defs/{definition}",
    }


RUN_REPORT_BODY_SCHEMA: dict[str, Any] = _operation_schema(
    "RunReportRequest",
    schema_id=("urn:marketing-tools:ga4datactl:schema:run-report-body.schema.json"),
    title="GA4 Data API v1beta RunReportRequest",
)
BATCH_RUN_REPORTS_BODY_SCHEMA: dict[str, Any] = _operation_schema(
    "BatchRunReportsRequest",
    schema_id=(
        "urn:marketing-tools:ga4datactl:schema:batch-run-reports-body.schema.json"
    ),
    title="GA4 Data API v1beta BatchRunReportsRequest",
)
BATCH_RUN_PIVOT_REPORTS_BODY_SCHEMA: dict[str, Any] = {
    **CORE_REPORTING_DEFINITIONS,
    "$id": "urn:marketing-tools:ga4datactl:schema:batch-run-pivot-reports-body.schema.json",
    "title": "GA4 Data API v1beta BatchRunPivotReportsRequest",
    "$ref": "#/$defs/BatchRunPivotReportsRequest",
    "$defs": {
        **CORE_REPORTING_DEFINITIONS["$defs"],
        "BatchRunPivotReportsRequest": {
            "additionalProperties": False,
            "description": "The batch request containing multiple pivot report requests.",
            "properties": {
                "requests": {
                    "description": (
                        "Individual pivot report requests. Each batch request is "
                        "allowed up to 5 requests."
                    ),
                    "items": {"$ref": "#/$defs/RunPivotReportRequest"},
                    "maxItems": 5,
                    "minItems": 1,
                    "type": "array",
                }
            },
            "type": "object",
        },
    },
}
RUN_PIVOT_REPORT_BODY_SCHEMA: dict[str, Any] = _operation_schema(
    "RunPivotReportRequest",
    schema_id=(
        "urn:marketing-tools:ga4datactl:schema:run-pivot-report-body.schema.json"
    ),
    title="GA4 Data API v1beta RunPivotReportRequest",
)

RUN_REALTIME_REPORT_BODY_SCHEMA: dict[str, Any] = {
    **CORE_REPORTING_DEFINITIONS,
    "$id": "urn:marketing-tools:ga4datactl:schema:run-realtime-report-body.schema.json",
    "title": "GA4 Data API v1beta RunRealtimeReportRequest",
    "$ref": "#/$defs/RunRealtimeReportRequest",
    "$defs": {
        **CORE_REPORTING_DEFINITIONS["$defs"],
        "MinuteRange": {
            "additionalProperties": False,
            "description": (
                "A contiguous range of realtime minutes. Standard properties "
                "support 0 through 29 minutes ago; GA360 properties support "
                "0 through 59."
            ),
            "properties": {
                "endMinutesAgo": {"maximum": 59, "minimum": 0, "type": "integer"},
                "name": {"type": "string"},
                "startMinutesAgo": {
                    "maximum": 59,
                    "minimum": 0,
                    "type": "integer",
                },
            },
            "type": "object",
        },
        "RunRealtimeReportRequest": {
            "additionalProperties": False,
            "description": "The request to generate a realtime report.",
            "properties": {
                "dimensionFilter": {"$ref": "#/$defs/FilterExpression"},
                "dimensions": {
                    "items": {"$ref": "#/$defs/Dimension"},
                    "maxItems": 9,
                    "type": "array",
                },
                "limit": {
                    "description": "A positive row limit no greater than 250,000.",
                    "format": "int64",
                    "pattern": "^[1-9][0-9]*$",
                    "type": "string",
                },
                "metricAggregations": {
                    "items": {
                        "enum": [
                            "METRIC_AGGREGATION_UNSPECIFIED",
                            "TOTAL",
                            "MINIMUM",
                            "MAXIMUM",
                            "COUNT",
                        ],
                        "type": "string",
                    },
                    "type": "array",
                },
                "metricFilter": {"$ref": "#/$defs/FilterExpression"},
                "metrics": {
                    "items": {"$ref": "#/$defs/Metric"},
                    "maxItems": 10,
                    "minItems": 1,
                    "type": "array",
                },
                "minuteRanges": {
                    "items": {"$ref": "#/$defs/MinuteRange"},
                    "maxItems": 2,
                    "type": "array",
                },
                "orderBys": {
                    "items": {"$ref": "#/$defs/OrderBy"},
                    "type": "array",
                },
                "returnPropertyQuota": {"type": "boolean"},
            },
            "required": ["metrics"],
            "type": "object",
        },
    },
}

CHECK_COMPATIBILITY_BODY_SCHEMA: dict[str, Any] = {
    **CORE_REPORTING_DEFINITIONS,
    "$id": "urn:marketing-tools:ga4datactl:schema:check-compatibility-body.schema.json",
    "title": "GA4 Data API v1beta CheckCompatibilityRequest",
    "$ref": "#/$defs/CheckCompatibilityRequest",
    "$defs": {
        **CORE_REPORTING_DEFINITIONS["$defs"],
        "CheckCompatibilityRequest": {
            "additionalProperties": False,
            "description": (
                "The request for compatibility information for a report's "
                "dimensions and metrics. Fields shared with RunReportRequest "
                "must use the same values as that report."
            ),
            "properties": {
                "dimensions": {
                    "description": "The dimensions in the candidate report.",
                    "items": {"$ref": "#/$defs/Dimension"},
                    "maxItems": 9,
                    "minItems": 1,
                    "type": "array",
                },
                "dimensionFilter": {"$ref": "#/$defs/FilterExpression"},
                "metrics": {
                    "description": "The metrics in the candidate report.",
                    "items": {"$ref": "#/$defs/Metric"},
                    "maxItems": 10,
                    "minItems": 1,
                    "type": "array",
                },
                "metricFilter": {"$ref": "#/$defs/FilterExpression"},
                "compatibilityFilter": {
                    "description": (
                        "Filters the response to compatible or incompatible "
                        "requested fields."
                    ),
                    "enum": [
                        "COMPATIBILITY_UNSPECIFIED",
                        "COMPATIBLE",
                        "INCOMPATIBLE",
                    ],
                    "type": "string",
                },
            },
            "anyOf": [
                {"required": ["dimensions"]},
                {"required": ["metrics"]},
            ],
            "type": "object",
        },
    },
}

CREATE_AUDIENCE_EXPORT_BODY_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:marketing-tools:ga4datactl:schema:create-audience-export-body.schema.json",
    "title": "GA4 Data API v1beta CreateAudienceExportRequest body",
    "description": (
        "The writable AudienceExport fields accepted by "
        "properties.audienceExports.create."
    ),
    "type": "object",
    "additionalProperties": False,
    "required": ["audience", "dimensions"],
    "properties": {
        "audience": {
            "description": (
                "The source audience resource name: "
                "properties/<property>/audiences/<audience>."
            ),
            "type": "string",
        },
        "dimensions": {
            "description": "The requested audience-export user attributes.",
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"dimensionName": {"type": "string"}},
            },
        },
    },
}
