-- NUMERIC columns of the enrichment tables (full data only).
-- Expect 19,120 non-null products.price and 888,623 non-null product_option_values.value_price,
-- with no value finer than the source (scale 9).
SELECT 'products.price' AS column_name, COUNT(price) AS non_null, MIN(price) AS min_value, MAX(price) AS max_value
FROM `{{dataset}}.products`
UNION ALL
SELECT 'product_option_values.value_price', COUNT(value_price), MIN(value_price), MAX(value_price)
FROM `{{dataset}}.product_option_values`;
