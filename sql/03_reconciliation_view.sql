USE ProduceDataQuality;
GO

CREATE OR ALTER VIEW dq.vw_ShipmentReconciliation
AS
SELECT
    s.shipment_id,
    s.product_id,
    p.product_name,
    s.shipment_date,
    s.shipped_kg,
    r.receipt_id,
    r.receipt_date,
    r.received_kg,

    -- Only calculate a difference when a valid receipt exists.
    CASE
        WHEN r.receipt_id IS NOT NULL
        THEN s.shipped_kg - r.received_kg
        ELSE NULL
    END AS shortfall_kg,

    CASE
        WHEN r.receipt_id IS NOT NULL
             AND r.received_kg = s.shipped_kg
            THEN 'MATCHED'

        WHEN r.receipt_id IS NOT NULL
            THEN 'QUANTITY_DISCREPANCY'

        WHEN EXISTS (
            SELECT 1
            FROM dq.RawRecord AS raw
            WHERE raw.run_id = source.run_id
              AND raw.source_file = 'receipts.csv'
              AND raw.record_status = 'REJECTED'
              AND LTRIM(RTRIM(
                  JSON_VALUE(raw.payload, '$.shipment_id')
              )) = s.shipment_id
        )
            THEN 'RECEIPT_DATA_ISSUE'

        ELSE 'PENDING_RECEIPT'
    END AS reconciliation_status,

    source.run_id
FROM dq.Shipment AS s
JOIN dq.Product AS p
    ON p.product_id = s.product_id
JOIN dq.RawRecord AS source
    ON source.raw_id = s.raw_id
LEFT JOIN dq.Receipt AS r
    ON r.shipment_id = s.shipment_id;
GO

-- Summarize the reconciliation results.
SELECT
    reconciliation_status,
    COUNT(*) AS shipment_count,
    SUM(shortfall_kg) AS total_shortfall_kg
FROM dq.vw_ShipmentReconciliation
GROUP BY reconciliation_status
ORDER BY reconciliation_status;

-- Inspect the valid deliveries with quantity differences.
SELECT
    shipment_id,
    product_name,
    shipped_kg,
    received_kg,
    shortfall_kg
FROM dq.vw_ShipmentReconciliation
WHERE reconciliation_status = 'QUANTITY_DISCREPANCY'
ORDER BY shipment_id;