-- Q8. How did total revenue build up over time, and how fast did it grow month on month?
WITH monthly AS (
    SELECT
        strftime('%Y-%m', o.order_purchase_timestamp)  AS month,
        SUM(i.price + i.freight_value)                 AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2)                                              AS revenue,
    ROUND(SUM(revenue) OVER (ORDER BY month), 2)                   AS cumulative_revenue,
    ROUND(100.0 * (revenue / LAG(revenue) OVER (ORDER BY month) - 1), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;
