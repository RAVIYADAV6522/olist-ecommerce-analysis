-- Q5. How much does a late delivery hurt the review score?
-- Some orders have more than one review, so scores are averaged per order first.
WITH order_scores AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
),
delivered AS (
    SELECT
        o.order_id,
        julianday(date(o.order_delivered_customer_date))
          - julianday(date(o.order_estimated_delivery_date)) AS days_late
    FROM orders AS o
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
)
SELECT
    CASE
        WHEN d.days_late <= 0  THEN '1. On time or early'
        WHEN d.days_late <= 3  THEN '2. 1-3 days late'
        WHEN d.days_late <= 7  THEN '3. 4-7 days late'
        WHEN d.days_late <= 14 THEN '4. 8-14 days late'
        ELSE                        '5. 15+ days late'
    END                                                       AS delay_bucket,
    COUNT(*)                                                  AS orders,
    ROUND(AVG(s.review_score), 2)                             AS avg_review_score,
    ROUND(100.0 * AVG(CASE WHEN s.review_score <= 2 THEN 1 ELSE 0 END), 1) AS pct_1_or_2_stars
FROM delivered AS d
JOIN order_scores AS s ON s.order_id = d.order_id
GROUP BY delay_bucket
ORDER BY delay_bucket;
