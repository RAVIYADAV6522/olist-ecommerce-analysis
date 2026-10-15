-- Q13. Do orders split across several sellers get worse reviews?
-- Multi-seller orders arrive in separate parcels, which may hurt the experience.
WITH order_sellers AS (
    SELECT i.order_id, COUNT(DISTINCT i.seller_id) AS sellers, COUNT(*) AS items
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
    GROUP BY i.order_id
),
order_scores AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
)
SELECT
    CASE WHEN os.sellers = 1 THEN '1 seller' ELSE '2+ sellers' END                AS sellers_in_order,
    COUNT(*)                                                                      AS orders,
    ROUND(AVG(os.items), 2)                                                       AS avg_items,
    ROUND(AVG(sc.review_score), 2)                                                AS avg_review_score,
    ROUND(100.0 * AVG(CASE WHEN sc.review_score <= 2 THEN 1 ELSE 0 END), 1)       AS pct_1_or_2_stars
FROM order_sellers AS os
JOIN order_scores AS sc ON sc.order_id = os.order_id
GROUP BY sellers_in_order
ORDER BY sellers_in_order;
