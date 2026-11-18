-- REQUIRED columns, partitioning and clustering as created from the contract (metadata only).
-- Expect: events partitioned by time_stamp and clustered by collection; REQUIRED columns kept after the load.
SELECT table_name, column_name, data_type, is_nullable, is_partitioning_column, clustering_ordinal_position
FROM `{{dataset}}.INFORMATION_SCHEMA.COLUMNS`
WHERE is_nullable = 'NO' OR is_partitioning_column = 'YES' OR clustering_ordinal_position IS NOT NULL
ORDER BY table_name, ordinal_position;
