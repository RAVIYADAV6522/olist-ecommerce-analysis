-- Q11. In which categories does shipping eat the biggest share of what the customer pays?
-- Only categories with at least 500 items, so small categories do not top the list by chance.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COUNT(*)                                                                     AS items,
    ROUND(AVG(i.price), 2)                                                       AS avg_price,
    ROUND(AVG(i.freight_value), 2)                                               AS avg_freight,
    ROUND(100.0 * SUM(i.freight_value) / SUM(i.price + i.freight_value), 1)      AS freight_pct_of_total
FROM order_items AS i
JOIN orders AS o                    ON o.order_id = i.order_id
JOIN products AS p                  ON p.product_id = i.product_id
LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY category
HAVING COUNT(*) >= 500
ORDER BY freight_pct_of_total DESC;
