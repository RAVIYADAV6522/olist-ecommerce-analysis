-- Q15. Which categories get the highest share of 1-star reviews, and is late delivery the reason?
-- Only categories with at least 1,000 reviewed orders.
WITH order_scores AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
),
order_category AS (
    -- An order is assigned to the category of its first item.
    SELECT
        o.order_id,
        COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
        CASE WHEN date(o.order_delivered_customer_date)
                > date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END             AS is_late
    FROM orders AS o
    JOIN order_items AS i               ON i.order_id = o.order_id AND i.order_item_id = 1
    JOIN products AS p                  ON p.product_id = i.product_id
    LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
)
SELECT
    oc.category,
    COUNT(*)                                                                AS reviewed_orders,
    ROUND(AVG(sc.review_score), 2)                                          AS avg_review_score,
    ROUND(100.0 * AVG(CASE WHEN sc.review_score = 1 THEN 1 ELSE 0 END), 1)  AS pct_1_star,
    ROUND(100.0 * AVG(oc.is_late), 1)                                       AS late_pct
FROM order_category AS oc
JOIN order_scores AS sc ON sc.order_id = oc.order_id
GROUP BY oc.category
HAVING COUNT(*) >= 1000
ORDER BY pct_1_star DESC;
