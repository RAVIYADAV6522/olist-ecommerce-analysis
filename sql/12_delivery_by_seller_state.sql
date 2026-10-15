-- Q12. Do sellers in some states ship more slowly or miss the estimate more often?
-- An order can have sellers in several states; each (order, seller state) pair counts once.
WITH order_seller_state AS (
    SELECT DISTINCT
        i.order_id,
        s.seller_state,
        julianday(o.order_delivered_carrier_date) - julianday(o.order_purchase_timestamp)  AS days_to_ship,
        julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS days_to_deliver,
        CASE WHEN date(o.order_delivered_customer_date)
                > date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END                 AS is_late
    FROM order_items AS i
    JOIN orders AS o  ON o.order_id = i.order_id
    JOIN sellers AS s ON s.seller_id = i.seller_id
    WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
    seller_state,
    COUNT(*)                           AS orders,
    ROUND(AVG(days_to_ship), 1)        AS avg_days_to_hand_to_carrier,
    ROUND(AVG(days_to_deliver), 1)     AS avg_days_to_customer,
    ROUND(100.0 * AVG(is_late), 1)     AS late_pct
FROM order_seller_state
GROUP BY seller_state
HAVING COUNT(*) >= 100
ORDER BY late_pct DESC;
