-- Q9. How do customers pay, and how often do they split payments into instalments?
-- SUM(...) OVER () is the grand total across all rows, used to turn counts into percentages.
SELECT
    p.payment_type,
    COUNT(*)                                                         AS payments,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)               AS pct_of_payments,
    ROUND(SUM(p.payment_value), 2)                                   AS payment_value,
    ROUND(100.0 * SUM(p.payment_value) / SUM(SUM(p.payment_value)) OVER (), 1) AS pct_of_value,
    ROUND(AVG(p.payment_installments), 1)                            AS avg_installments,
    ROUND(100.0 * AVG(CASE WHEN p.payment_installments > 1 THEN 1 ELSE 0 END), 1) AS pct_in_installments
FROM payments AS p
JOIN orders AS o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
  AND p.payment_type <> 'not_defined'
GROUP BY p.payment_type
ORDER BY payments DESC;
