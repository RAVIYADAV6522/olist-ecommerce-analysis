-- Q7. Who are the top 3 sellers by revenue in each seller state?
-- RANK() restarts at 1 for every state because of PARTITION BY.
WITH seller_revenue AS (
    SELECT
        s.seller_state,
        s.seller_id,
        COUNT(DISTINCT o.order_id)                AS orders,
        ROUND(SUM(i.price + i.freight_value), 2)  AS revenue
    FROM order_items AS i
    JOIN orders AS o  ON o.order_id = i.order_id
    JOIN sellers AS s ON s.seller_id = i.seller_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
    GROUP BY s.seller_state, s.seller_id
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY seller_state ORDER BY revenue DESC) AS state_rank
    FROM seller_revenue
)
SELECT seller_state, state_rank, seller_id, orders, revenue
FROM ranked
WHERE state_rank <= 3
ORDER BY seller_state, state_rank;
