\# Data Dictionary



\## products.csv



| Column | Description | Type | Rule |

|---|---|---|---|

| product\_id | Unique produce product identifier | Text | Required and unique |

| product\_name | Produce name | Text | Required |

| unit | Measurement unit | Text | Must equal `kg` |



\## shipments.csv



| Column | Description | Type | Rule |

|---|---|---|---|

| shipment\_id | Unique shipment identifier | Text | Required and unique |

| product\_id | Product reference | Text | Must exist in accepted products |

| shipment\_date | Date shipment left the facility | Date | Format `YYYY-MM-DD` |

| shipped\_kg | Quantity shipped | Decimal | Must be non-negative |



\## receipts.csv



| Column | Description | Type | Rule |

|---|---|---|---|

| receipt\_id | Unique receipt identifier | Text | Required and unique |

| shipment\_id | Shipment reference | Text | Must exist in accepted shipments |

| receipt\_date | Date shipment was received | Date | Must not precede shipment date |

| received\_kg | Quantity received | Decimal | Must not exceed shipped quantity |



\## SQL Audit Tables



\- `dq.PipelineRun` — pipeline execution and reconciliation totals

\- `dq.RawRecord` — original source payload and processing status

\- `dq.ValidationIssue` — rejected-record rule codes and descriptions

\- `dq.Product` — accepted product records

\- `dq.Shipment` — accepted shipment records

\- `dq.Receipt` — accepted receipt records

