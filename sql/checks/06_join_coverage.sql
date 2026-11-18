-- Joins the analytics depend on (full data only).
-- Expect about 98.88% of events with a resolved location, and about 1.5% of product references without attributes.
SELECT
  'events with a resolved IP location' AS check_name,
  ROUND(100 * COUNTIF(l.status = 'resolved') / COUNT(*), 2) AS percent
FROM `{{dataset}}.events` AS e
LEFT JOIN `{{dataset}}.ip_locations` AS l USING (ip_hash)
UNION ALL
SELECT
  'events.product_id without product attributes',
  ROUND(100 * COUNTIF(p.status IS DISTINCT FROM 'success') / COUNT(*), 2)
FROM `{{dataset}}.events` AS e
LEFT JOIN `{{dataset}}.products` AS p USING (product_id)
WHERE e.product_id IS NOT NULL;
