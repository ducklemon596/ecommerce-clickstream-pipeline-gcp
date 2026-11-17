-- Rows and size per table (metadata only, no bytes scanned). Expect each row_count to equal its _manifest.json rows.
SELECT table_id, row_count, ROUND(size_bytes / POW(10, 9), 2) AS size_gb
FROM `{{dataset}}.__TABLES__`
ORDER BY table_id;
