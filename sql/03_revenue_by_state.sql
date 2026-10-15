-- Q3. Which customer states bring in the most revenue, and what is their average order value?
-- HAVING drops states with too few orders for the average to mean much.
SELECT
    c.customer_state                                                       AS state,
    COUNT(DISTINCT o.order_id)                                             AS orders,
    ROUND(SUM(i.price + i.freight_value), 2)                               AS revenue,
    ROUND(SUM(i.price + i.freight_value) / COUNT(DISTINCT o.order_id), 2)  AS avg_order_value
FROM orders AS o
JOIN customers AS c   ON c.customer_id = o.customer_id
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY state
HAVING COUNT(DISTINCT o.order_id) >= 100
ORDER BY revenue DESC;
