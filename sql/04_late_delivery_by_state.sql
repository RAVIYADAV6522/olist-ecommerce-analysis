-- Q4. In which states are orders most often delivered after the estimated date?
-- Late = delivered on a later calendar day than estimated (the estimate has no time of day).
SELECT
    c.customer_state                                                            AS state,
    COUNT(*)                                                                    AS delivered_orders,
    SUM(CASE WHEN date(o.order_delivered_customer_date)
                > date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END)      AS late_orders,
    ROUND(100.0 * AVG(CASE WHEN date(o.order_delivered_customer_date)
                > date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END), 1)  AS late_pct,
    ROUND(AVG(julianday(o.order_delivered_customer_date)
            - julianday(o.order_purchase_timestamp)), 1)                        AS avg_delivery_days
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY state
ORDER BY late_pct DESC;
