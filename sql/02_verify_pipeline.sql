USE ProduceDataQuality;
GO

DECLARE @RunId INT = (
    SELECT MAX(run_id)
    FROM dq.PipelineRun
    WHERE status = 'SUCCESS'
);

-- 1. Confirm the recorded run totals.
SELECT
    run_id,
    status,
    input_count,
    accepted_count,
    rejected_count
FROM dq.PipelineRun
WHERE run_id = @RunId;

-- 2. Independently count the actual raw-record outcomes.
SELECT
    source_file,
    COUNT(*) AS input_records,
    SUM(CASE WHEN record_status = 'ACCEPTED' THEN 1 ELSE 0 END)
        AS accepted_records,
    SUM(CASE WHEN record_status = 'REJECTED' THEN 1 ELSE 0 END)
        AS rejected_records,
    SUM(CASE WHEN record_status = 'PENDING' THEN 1 ELSE 0 END)
        AS pending_records
FROM dq.RawRecord
WHERE run_id = @RunId
GROUP BY source_file
ORDER BY source_file;

-- 3. Check the accepted tables.
SELECT 'Product' AS table_name, COUNT(*) AS record_count
FROM dq.Product
UNION ALL
SELECT 'Shipment', COUNT(*) FROM dq.Shipment
UNION ALL
SELECT 'Receipt', COUNT(*) FROM dq.Receipt;

-- 4. Show which source rows failed and why.
SELECT
    r.source_file,
    r.source_row,
    i.rule_code,
    i.issue_description
FROM dq.RawRecord AS r
JOIN dq.ValidationIssue AS i
    ON i.raw_id = r.raw_id
WHERE r.run_id = @RunId
ORDER BY r.source_file, r.source_row, i.rule_code;