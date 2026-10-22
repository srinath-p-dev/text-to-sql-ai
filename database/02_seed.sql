-- ==============================================
-- 02_seed.sql
-- Loads deterministic sample data into the
-- empty store_db tables created by
-- 01_schema.sql.
--
-- Run against store_db. Type this as ONE
-- command on ONE line:
--   psql -U postgres -d store_db
--        -v ON_ERROR_STOP=1
--        -f database/02_seed.sql
--
-- SAFETY: This script only ADDS rows. It never
-- deletes, updates, or truncates anything.
-- It uses fixed IDs, so running it a second
-- time fails on a duplicate primary key, and
-- because everything runs inside one
-- transaction, no rows from that run are
-- saved. (Note: sequence changes made by
-- setval() are NOT rolled back; see
-- section 5.)
--
-- Expected result (non-cancelled orders only):
--   total revenue = 1795.00
-- ==============================================

BEGIN;

-- ----------------------------------------------
-- 1. customers (12 rows)
--    Kofi (11) has no orders.
--    Lina (12) has only a cancelled order.
-- ----------------------------------------------
INSERT INTO customers
    (customer_id, full_name, email,
     city, country, signup_date)
VALUES
    (1, 'Asha Rao',
        'asha.rao@example.com',
        'Bengaluru', 'India', '2024-11-02'),
    (2, 'Ben Clark',
        'ben.clark@example.com',
        'Leeds', 'UK', '2024-11-15'),
    (3, 'Carmen Diaz',
        'carmen.diaz@example.com',
        'Madrid', 'Spain', '2024-12-01'),
    (4, 'David Kim',
        'david.kim@example.com',
        'Seoul', 'South Korea', '2024-12-10'),
    (5, 'Emma Wilson',
        'emma.wilson@example.com',
        'Toronto', 'Canada', '2025-01-05'),
    (6, 'Farah Khan',
        'farah.khan@example.com',
        'Mumbai', 'India', '2025-01-12'),
    (7, 'George Brown',
        'george.brown@example.com',
        'London', 'UK', '2025-01-20'),
    (8, 'Hana Sato',
        'hana.sato@example.com',
        'Tokyo', 'Japan', '2025-02-03'),
    (9, 'Ivan Petrov',
        'ivan.petrov@example.com',
        'Sofia', 'Bulgaria', '2025-02-14'),
    (10, 'Julia Rossi',
        'julia.rossi@example.com',
        'Rome', 'Italy', '2025-02-25'),
    (11, 'Kofi Mensah',
        'kofi.mensah@example.com',
        'Accra', 'Ghana', '2025-03-08'),
    (12, 'Lina Haddad',
        'lina.haddad@example.com',
        'Dubai', 'UAE', '2025-03-20');

-- ----------------------------------------------
-- 2. products (12 rows)
--    Phone Stand (12) is never sold.
--    price = CURRENT list price. Some items
--    sold for less in the past (see 4.).
-- ----------------------------------------------
INSERT INTO products
    (product_id, product_name, category,
     price, stock_qty)
VALUES
    (1, 'Wireless Mouse',
        'Electronics', 25.00, 120),
    (2, 'Mechanical Keyboard',
        'Electronics', 80.00, 45),
    (3, 'USB-C Charger',
        'Electronics', 30.00, 200),
    (4, 'Bluetooth Headphones',
        'Electronics', 120.00, 30),
    (5, 'Coffee Mug',
        'Home', 12.00, 300),
    (6, 'Desk Lamp',
        'Home', 45.00, 60),
    (7, 'Throw Pillow',
        'Home', 20.00, 80),
    (8, 'A5 Notebook',
        'Stationery', 5.00, 500),
    (9, 'Gel Pen Set',
        'Stationery', 8.00, 400),
    (10, 'Backpack',
        'Accessories', 60.00, 50),
    (11, 'Water Bottle',
        'Accessories', 18.00, 150),
    (12, 'Phone Stand',
        'Electronics', 15.00, 90);

-- ----------------------------------------------
-- 3. orders (20 rows, Jan-Apr 2025)
--    13 delivered, 3 shipped, 2 pending,
--    2 cancelled (orders 5 and 15).
-- ----------------------------------------------
INSERT INTO orders
    (order_id, customer_id, order_date, status)
VALUES
    -- January 2025
    ( 1,  1, '2025-01-08', 'delivered'), -- Asha
    ( 2,  2, '2025-01-12', 'delivered'), -- Ben
    ( 3,  3, '2025-01-19', 'delivered'), -- Carmen
    ( 4,  1, '2025-01-26', 'delivered'), -- Asha
    ( 5,  4, '2025-01-30', 'cancelled'), -- David
    -- February 2025
    ( 6,  5, '2025-02-03', 'delivered'), -- Emma
    ( 7,  2, '2025-02-09', 'delivered'), -- Ben
    ( 8,  6, '2025-02-14', 'delivered'), -- Farah
    ( 9,  3, '2025-02-20', 'delivered'), -- Carmen
    (10,  7, '2025-02-27', 'delivered'), -- George
    -- March 2025
    (11,  1, '2025-03-04', 'delivered'), -- Asha
    (12,  8, '2025-03-10', 'delivered'), -- Hana
    (13,  4, '2025-03-15', 'delivered'), -- David
    (14,  9, '2025-03-21', 'shipped'),   -- Ivan
    (15, 12, '2025-03-25', 'cancelled'), -- Lina
    (16,  5, '2025-03-29', 'delivered'), -- Emma
    -- April 2025
    (17,  2, '2025-04-02', 'shipped'),   -- Ben
    (18, 10, '2025-04-08', 'shipped'),   -- Julia
    (19,  6, '2025-04-14', 'pending'),   -- Farah
    (20,  3, '2025-04-18', 'pending');   -- Carmen

-- ----------------------------------------------
-- 4. order_items (36 rows)
--    Columns: item, order, product, qty, price
--    unit_price = price ACTUALLY PAID.
--    Two items sold below today's list price:
--      item  1: Keyboard   75.00 (list 80.00)
--      item 13: Headphones 100.00 (list 120.00)
-- ----------------------------------------------
INSERT INTO order_items
    (order_item_id, order_id, product_id,
     quantity, unit_price)
VALUES
    -- order 1: Asha = 100.00
    ( 1,  1,  2,  1,  75.00), -- Keyboard
    ( 2,  1,  1,  1,  25.00), -- Mouse
    -- order 2: Ben = 73.00
    ( 3,  2,  5,  4,  12.00), -- Mug
    ( 4,  2,  8,  5,   5.00), -- Notebook
    -- order 3: Carmen = 120.00
    ( 5,  3,  4,  1, 120.00), -- Headphones
    -- order 4: Asha = 68.00
    ( 6,  4,  3,  2,  30.00), -- Charger
    ( 7,  4,  9,  1,   8.00), -- Pen Set
    -- order 5: David = 60.00 (CANCELLED)
    ( 8,  5, 10,  1,  60.00), -- Backpack
    -- order 6: Emma = 85.00
    ( 9,  6,  6,  1,  45.00), -- Lamp
    (10,  6,  7,  2,  20.00), -- Pillow
    -- order 7: Ben = 130.00
    (11,  7,  2,  1,  80.00), -- Keyboard
    (12,  7,  1,  2,  25.00), -- Mouse
    -- order 8: Farah = 118.00
    (13,  8,  4,  1, 100.00), -- Headphones
    (14,  8, 11,  1,  18.00), -- Bottle
    -- order 9: Carmen = 74.00
    (15,  9,  8, 10,   5.00), -- Notebook
    (16,  9,  9,  3,   8.00), -- Pen Set
    -- order 10: George = 96.00
    (17, 10, 10,  1,  60.00), -- Backpack
    (18, 10, 11,  2,  18.00), -- Bottle
    -- order 11: Asha = 150.00
    (19, 11,  4,  1, 120.00), -- Headphones
    (20, 11,  3,  1,  30.00), -- Charger
    -- order 12: Hana = 69.00
    (21, 12,  5,  2,  12.00), -- Mug
    (22, 12,  6,  1,  45.00), -- Lamp
    -- order 13: David = 80.00
    (23, 13,  2,  1,  80.00), -- Keyboard
    -- order 14: Ivan = 61.00
    (24, 14,  1,  1,  25.00), -- Mouse
    (25, 14,  8,  4,   5.00), -- Notebook
    (26, 14,  9,  2,   8.00), -- Pen Set
    -- order 15: Lina = 90.00 (CANCELLED)
    (27, 15,  6,  2,  45.00), -- Lamp
    -- order 16: Emma = 114.00
    (28, 16, 11,  3,  18.00), -- Bottle
    (29, 16, 10,  1,  60.00), -- Backpack
    -- order 17: Ben = 240.00
    (30, 17,  4,  2, 120.00), -- Headphones
    -- order 18: Julia = 72.00
    (31, 18,  7,  3,  20.00), -- Pillow
    (32, 18,  5,  1,  12.00), -- Mug
    -- order 19: Farah = 55.00
    (33, 19,  3,  1,  30.00), -- Charger
    (34, 19,  1,  1,  25.00), -- Mouse
    -- order 20: Carmen = 90.00
    (35, 20,  2,  1,  80.00), -- Keyboard
    (36, 20,  8,  2,   5.00); -- Notebook

-- ----------------------------------------------
-- 5. Sync the identity counters (sequences).
--    We supplied our own IDs, so each counter
--    still thinks the next ID is 1. Move each
--    one to the highest ID in use, so the next
--    automatic ID is MAX + 1.
--    Changes counter positions only; no rows.
--    setval() is NOT undone by a rollback.
-- ----------------------------------------------
SELECT setval(
    pg_get_serial_sequence('customers',
                           'customer_id'),
    (SELECT MAX(customer_id) FROM customers));

SELECT setval(
    pg_get_serial_sequence('products',
                           'product_id'),
    (SELECT MAX(product_id) FROM products));

SELECT setval(
    pg_get_serial_sequence('orders',
                           'order_id'),
    (SELECT MAX(order_id) FROM orders));

SELECT setval(
    pg_get_serial_sequence('order_items',
                           'order_item_id'),
    (SELECT MAX(order_item_id) FROM order_items));

COMMIT;
