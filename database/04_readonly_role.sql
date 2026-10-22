-- ==============================================
-- 04_readonly_role.sql
-- Creates a limited, read-only database user
-- for the app.
--
-- Run from PowerShell as postgres (ONE line):
--   psql -U postgres -d store_db -v ON_ERROR_STOP=1 -f database/04_readonly_role.sql
--
-- The password is NOT set here, so it never ends
-- up in Git. Set it afterwards inside psql with:
--   \password app_readonly
-- ==============================================

BEGIN;

-- 1. Create the user (can log in once a password is set)
CREATE ROLE app_readonly LOGIN;

-- 2. Allow it to connect to this database
GRANT CONNECT ON DATABASE store_db TO app_readonly;

-- 3. Allow it to see the tables in the public schema
GRANT USAGE ON SCHEMA public TO app_readonly;

-- 4. Allow it to READ the 4 tables, and nothing else
GRANT SELECT ON customers, products, orders, order_items
    TO app_readonly;

-- 5. Make every session for this user read-only by default
ALTER ROLE app_readonly SET default_transaction_read_only = on;

-- 6. Stop any single query from this user after 5 seconds
ALTER ROLE app_readonly SET statement_timeout = '5s';

COMMIT;
