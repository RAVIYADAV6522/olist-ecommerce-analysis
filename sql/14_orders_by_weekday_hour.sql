-- Q14. When do customers shop? Orders by day of week and hour of day (168 rows, for a heatmap).
-- strftime('%w') returns 0 for Sunday through 6 for Saturday.
SELECT
    CAST(strftime('%w', o.order_purchase_timestamp) AS INTEGER)   AS weekday_num,
    CASE strftime('%w', o.order_purchase_timestamp)
        WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue'
        WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri'
        ELSE 'Sat'
    END                                                           AS weekday,
    CAST(strftime('%H', o.order_purchase_timestamp) AS INTEGER)   AS hour,
    COUNT(*)                                                      AS orders
FROM orders AS o
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY weekday_num, hour
ORDER BY weekday_num, hour;
