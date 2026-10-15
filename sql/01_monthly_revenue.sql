-- Q1. How did revenue and order volume trend month by month?
-- Revenue = item price + freight, delivered orders only, Jan 2017 – Aug 2018.
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp)       AS month,
    COUNT(DISTINCT o.order_id)                           AS orders,
    ROUND(SUM(i.price + i.freight_value), 2)             AS revenue
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY month
ORDER BY month;
