-- Q6. What share of customers placed more than one order?
-- customer_id is new for every order; customer_unique_id identifies the actual person.
WITH orders_per_customer AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*)                                                         AS customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)                 AS repeat_customers,
    ROUND(100.0 * AVG(CASE WHEN order_count > 1 THEN 1 ELSE 0 END), 2) AS repeat_pct,
    MAX(order_count)                                                 AS most_orders_by_one_customer
FROM orders_per_customer;
