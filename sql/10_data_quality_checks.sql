-- Q10. What problems are in the raw data? One row per check, with how many rows fail it.
-- Runs on the whole dataset (no date or status filter) so nothing is hidden.
SELECT 'Delivered orders with no delivery date' AS check_name, COUNT(*) AS failing_rows
FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL
UNION ALL
SELECT 'Orders delivered before they were purchased', COUNT(*)
FROM orders WHERE order_delivered_customer_date < order_purchase_timestamp
UNION ALL
SELECT 'Orders approved before they were purchased', COUNT(*)
FROM orders WHERE order_approved_at < order_purchase_timestamp
UNION ALL
SELECT 'Orders handed to carrier before purchase', COUNT(*)
FROM orders WHERE order_delivered_carrier_date < order_purchase_timestamp
UNION ALL
SELECT 'Orders with no items', COUNT(*)
FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM order_items AS i WHERE i.order_id = o.order_id)
UNION ALL
SELECT 'Orders with no payment', COUNT(*)
FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM payments AS p WHERE p.order_id = o.order_id)
UNION ALL
SELECT 'Items where freight costs more than the item', COUNT(*)
FROM order_items WHERE freight_value > price
UNION ALL
SELECT 'Items with zero or negative price', COUNT(*)
FROM order_items WHERE price <= 0
UNION ALL
SELECT 'Products with no category', COUNT(*)
FROM products WHERE product_category_name IS NULL
UNION ALL
SELECT 'Products whose category has no English name', COUNT(*)
FROM products AS p
WHERE p.product_category_name IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM category_translation AS t
                  WHERE t.product_category_name = p.product_category_name)
UNION ALL
SELECT 'Orders with more than one review', COUNT(*)
FROM (SELECT order_id FROM reviews GROUP BY order_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'Customer IDs that belong to a repeat person', COUNT(*) - COUNT(DISTINCT customer_unique_id)
FROM customers;
