-- Q2. Which 10 product categories bring in the most revenue?
-- LEFT JOINs keep products with no category or no English translation instead of dropping them.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COUNT(DISTINCT o.order_id)                                                   AS orders,
    ROUND(SUM(i.price + i.freight_value), 2)                                     AS revenue,
    ROUND(SUM(i.price + i.freight_value) / COUNT(DISTINCT o.order_id), 2)        AS avg_order_value
FROM orders AS o
JOIN order_items AS i           ON i.order_id = o.order_id
JOIN products AS p              ON p.product_id = i.product_id
LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;
