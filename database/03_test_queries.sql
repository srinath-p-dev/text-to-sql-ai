-- ==============================================
-- 03_test_queries.sql
-- Read-only checks that the seed data matches
-- the expected values.
--
-- Run from PowerShell (ONE line):
--   psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/03_test_queries.sql
--
-- SAFETY: Runs inside a READ ONLY transaction
-- and ends with ROLLBACK. Nothing is changed.
--
-- Revenue rule: SUM(quantity * unit_price),
-- excluding orders with status = 'cancelled'.
-- ==============================================

BEGIN TRANSACTION READ ONLY;

-- 1. Row counts
-- Expected: customers 12, products 12, orders 20, order_items 36
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'products',    COUNT(*) FROM products
UNION ALL SELECT 'orders',      COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;

-- 2. Total non-cancelled revenue
-- Expected: 1795.00
SELECT SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status <> 'cancelled';

-- 3. Top five customers by non-cancelled revenue
-- Expected: Ben Clark 443.00, Asha Rao 318.00, Carmen Diaz 284.00,
--           Emma Wilson 199.00, Farah Khan 173.00
SELECT c.full_name, SUM(oi.quantity * oi.unit_price) AS revenue
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
WHERE o.status <> 'cancelled'
GROUP BY c.customer_id, c.full_name
ORDER BY revenue DESC, c.full_name
LIMIT 5;

-- 4. Monthly revenue
-- Expected: 2025-01 361.00, 2025-02 503.00, 2025-03 474.00, 2025-04 457.00
SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS month,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'cancelled'
GROUP BY month
ORDER BY month;

-- 5. Customers with no orders at all
-- Expected: Kofi Mensah
SELECT c.customer_id, c.full_name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
)
ORDER BY c.customer_id;

-- 6. Products never sold
-- Expected: Phone Stand
SELECT p.product_id, p.product_name
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id
)
ORDER BY p.product_id;

-- 7. Revenue by product category
-- Expected: Electronics 1140.00, Home 274.00, Accessories 228.00, Stationery 153.00
SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o       ON o.order_id    = oi.order_id
WHERE o.status <> 'cancelled'
GROUP BY p.category
ORDER BY revenue DESC;

-- 8. Customers with zero non-cancelled revenue
-- Expected: Kofi Mensah, Lina Haddad (both 0)
SELECT c.full_name,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
FROM customers c
LEFT JOIN orders o       ON o.customer_id = c.customer_id
                        AND o.status <> 'cancelled'
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.full_name
HAVING COALESCE(SUM(oi.quantity * oi.unit_price), 0) = 0
ORDER BY c.full_name;

-- 9. Order counts by status
-- Expected: delivered 13, shipped 3, cancelled 2, pending 2
SELECT status, COUNT(*) AS order_count
FROM orders
GROUP BY status
ORDER BY order_count DESC, status;

ROLLBACK;
