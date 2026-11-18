-- Arrays, the nullable STRUCT and timestamps as loaded.
-- Full-data expectations from the contract: option_filter set on ~12.09 M listing events (their option is []),
-- 148,509 cart lines with an empty option array, time_stamp from 2020-04-01 00:00:01 to 2020-06-04 10:21:32 UTC.
SELECT
  COUNT(*) AS events,
  COUNTIF(ARRAY_LENGTH(option) > 0) AS with_option_array,
  COUNTIF(option_filter IS NOT NULL) AS with_option_filter,
  COUNTIF(option_filter IS NOT NULL AND ARRAY_LENGTH(option) = 0) AS filter_with_empty_option,
  (SELECT COUNT(*) FROM `{{dataset}}.events`, UNNEST(cart_products) AS line WHERE ARRAY_LENGTH(line.option) = 0)
    AS cart_lines_with_empty_option,
  MIN(time_stamp) AS first_event,
  MAX(time_stamp) AS last_event
FROM `{{dataset}}.events`;
