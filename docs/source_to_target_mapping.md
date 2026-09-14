\# Source-to-Target Mapping



\## Products



| Source field | Target table | Target column | Transformation |

|---|---|---|---|

| products.csv.product\_id | dq.Product | product\_id | Trim whitespace; validate required and unique |

| products.csv.product\_name | dq.Product | product\_name | Trim whitespace; validate required |

| products.csv.unit | dq.Product | unit | Trim whitespace; validate value equals `kg` |

| Source row and payload | dq.RawRecord | source\_row, payload | Preserve original source record for audit |



\## Shipments



| Source field | Target table | Target column | Transformation |

|---|---|---|---|

| shipments.csv.shipment\_id | dq.Shipment | shipment\_id | Trim whitespace; validate required and unique |

| shipments.csv.product\_id | dq.Shipment | product\_id | Validate product reference |

| shipments.csv.shipment\_date | dq.Shipment | shipment\_date | Parse strict `YYYY-MM-DD` date |

| shipments.csv.shipped\_kg | dq.Shipment | shipped\_kg | Parse decimal; reject negative values |

| Source row and payload | dq.RawRecord | source\_row, payload | Preserve original source record for audit |



\## Receipts



| Source field | Target table | Target column | Transformation |

|---|---|---|---|

| receipts.csv.receipt\_id | dq.Receipt | receipt\_id | Trim whitespace; validate required and unique |

| receipts.csv.shipment\_id | dq.Receipt | shipment\_id | Validate shipment reference |

| receipts.csv.receipt\_date | dq.Receipt | receipt\_date | Parse date; must not precede shipment date |

| receipts.csv.received\_kg | dq.Receipt | received\_kg | Parse decimal; must not exceed shipped quantity |

| Source row and payload | dq.RawRecord | source\_row, payload | Preserve original source record for audit |



\## Rejected Records



Rows failing validation are not loaded into accepted target tables. They remain in `dq.RawRecord` with status `REJECTED`, and each failed rule is written to `dq.ValidationIssue`.

