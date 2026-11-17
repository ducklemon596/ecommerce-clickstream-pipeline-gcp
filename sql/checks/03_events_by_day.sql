-- Rows per UTC day of the _id ObjectId time (the export's chunks) and per day of time_stamp.
-- Expect: rows_by_id_day equal to the chunk rows in _manifest.json; the two days differ for 166 rows in the full data.
WITH days AS (
  SELECT DATE(TIMESTAMP_SECONDS(CAST(CONCAT('0x', SUBSTR(_id, 1, 8)) AS INT64))) AS id_day,
         DATE(time_stamp) AS event_day
  FROM `{{dataset}}.events`
)
SELECT id_day,
       COUNT(*) AS rows_by_id_day,
       COUNTIF(event_day != id_day) AS time_stamp_on_other_day
FROM days
GROUP BY id_day
ORDER BY id_day;
