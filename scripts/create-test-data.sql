-- PostgreSQL Simple Test Data Generator
-- Creates minimal but comprehensive test data for MCP PostgreSQL Operations Server
-- Designed to avoid foreign key constraint violations

-- =============================================================================
-- CLEAN UP AND PREPARATION
-- =============================================================================
\echo 'Starting simple test data creation...'
\echo 'First, cleaning up any existing sample databases and users...'

-- Temporarily disable error stopping to handle cases where databases/users don't exist
\set ON_ERROR_STOP off

-- Disconnect all users from test databases before dropping them
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname IN ('ecommerce', 'analytics', 'inventory', 'hr_system')
  AND pid <> pg_backend_pid();

-- Drop existing test databases (including any that might conflict with POSTGRES_DB)
\echo 'Dropping sample databases if they exist...'
DROP DATABASE IF EXISTS ecommerce;
DROP DATABASE IF EXISTS analytics;
DROP DATABASE IF EXISTS inventory;
DROP DATABASE IF EXISTS hr_system;

-- Drop existing test users
\echo 'Dropping sample users if they exist...'
DROP USER IF EXISTS app_readonly;
DROP USER IF EXISTS app_readwrite;
DROP USER IF EXISTS analytics_user;
DROP USER IF EXISTS backup_user;

-- Re-enable error stopping for the rest of the script
\set ON_ERROR_STOP on

\echo 'Cleanup completed. Now creating fresh databases and users...'

-- =============================================================================
-- CREATE DATABASES AND USERS
-- =============================================================================

-- Create databases
CREATE DATABASE ecommerce WITH ENCODING = 'UTF8';
CREATE DATABASE analytics WITH ENCODING = 'UTF8';
CREATE DATABASE inventory WITH ENCODING = 'UTF8';
CREATE DATABASE hr_system WITH ENCODING = 'UTF8';

-- Create users
CREATE USER app_readonly WITH PASSWORD 'readonly123';
CREATE USER app_readwrite WITH PASSWORD 'readwrite123';
CREATE USER analytics_user WITH PASSWORD 'analytics123';
CREATE USER backup_user WITH PASSWORD 'backup123';

-- Grant database access
GRANT CONNECT ON DATABASE ecommerce TO app_readonly, app_readwrite;
GRANT CONNECT ON DATABASE analytics TO analytics_user;
GRANT CONNECT ON DATABASE inventory TO app_readwrite;
GRANT CONNECT ON DATABASE hr_system TO app_readwrite;

-- =============================================================================
-- ECOMMERCE DATABASE
-- =============================================================================
\c ecommerce

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO app_readonly, app_readwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;

-- Categories (fixed 5 categories)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categories (name) VALUES
('Electronics'),
('Books'),
('Clothing'),
('Home'),
('Sports');

-- Products (50 products, 10 per category)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, price, category_id)
SELECT 
    'Product ' || generate_series,
    (10 + (generate_series % 100))::decimal(10,2),
    ((generate_series - 1) / 10) + 1  -- Safe category assignment: 1-5
FROM generate_series(1, 50);

-- Customers (100 customers)
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (email, first_name, last_name)
SELECT 
    'user' || generate_series || '@example.com',
    'First' || generate_series,
    'Last' || generate_series
FROM generate_series(1, 100);

-- Orders (200 orders, safe customer references)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed',
    total_amount DECIMAL(12,2) DEFAULT 100.00
);

INSERT INTO orders (customer_id, total_amount)
SELECT 
    ((generate_series - 1) % 100) + 1,  -- Safe customer_id: 1-100
    (50 + (generate_series % 200))::decimal(12,2)
FROM generate_series(1, 200);

-- Order Items (400 items, safe references)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2) DEFAULT 50.00
);

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT 
    ((generate_series - 1) % 200) + 1,  -- Safe order_id: 1-200
    ((generate_series - 1) % 50) + 1,   -- Safe product_id: 1-50
    1 + (generate_series % 3),          -- quantity: 1-3
    (20 + (generate_series % 80))::decimal(10,2)
FROM generate_series(1, 400);

-- Create indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

\echo 'Ecommerce database created with safe data';

-- =============================================================================
-- ANALYTICS DATABASE
-- =============================================================================
\c analytics

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Page Views (1000 records)
CREATE TABLE page_views (
    id SERIAL PRIMARY KEY,
    page_url VARCHAR(200) NOT NULL,
    view_count INTEGER DEFAULT 1,
    view_date DATE DEFAULT CURRENT_DATE
);

INSERT INTO page_views (page_url, view_count, view_date)
SELECT 
    '/page/' || generate_series,
    1 + (generate_series % 100),
    CURRENT_DATE - (generate_series % 30)
FROM generate_series(1, 1000);

-- Sales Summary (30 days)
CREATE TABLE sales_summary (
    id SERIAL PRIMARY KEY,
    date_key DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.00
);

INSERT INTO sales_summary (date_key, total_orders, total_revenue)
SELECT 
    CURRENT_DATE - generate_series,
    10 + (generate_series % 20),
    (1000 + (generate_series * 50))::decimal(12,2)
FROM generate_series(0, 29);

CREATE INDEX idx_page_views_date ON page_views(view_date);
CREATE INDEX idx_sales_summary_date ON sales_summary(date_key);

\echo 'Analytics database created with safe data';

-- =============================================================================
-- INVENTORY DATABASE
-- =============================================================================
\c inventory

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
GRANT USAGE ON SCHEMA public TO app_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;

-- Suppliers (10 suppliers)
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO suppliers (name, contact_email)
SELECT 
    'Supplier Company ' || generate_series,
    'supplier' || generate_series || '@company.com'
FROM generate_series(1, 10);

-- Inventory Items (100 items, safe supplier references)
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    unit_cost DECIMAL(10,2) DEFAULT 25.00,
    stock_quantity INTEGER DEFAULT 100
);

INSERT INTO inventory_items (sku, name, supplier_id, unit_cost, stock_quantity)
SELECT 
    'SKU' || LPAD(generate_series::text, 4, '0'),
    'Item ' || generate_series,
    ((generate_series - 1) % 10) + 1,  -- Safe supplier_id: 1-10
    (10 + (generate_series % 50))::decimal(10,2),
    50 + (generate_series % 100)
FROM generate_series(1, 100);

-- Purchase Orders (50 orders, safe supplier references)
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    order_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(12,2) DEFAULT 1000.00
);

INSERT INTO purchase_orders (po_number, supplier_id, total_amount)
SELECT 
    'PO' || LPAD(generate_series::text, 4, '0'),
    ((generate_series - 1) % 10) + 1,  -- Safe supplier_id: 1-10
    (500 + (generate_series * 100))::decimal(12,2)
FROM generate_series(1, 50);

CREATE INDEX idx_inventory_items_supplier ON inventory_items(supplier_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);

\echo 'Inventory database created with safe data';

-- =============================================================================
-- HR SYSTEM DATABASE
-- =============================================================================
\c hr_system

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
GRANT USAGE ON SCHEMA public TO app_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;

-- Departments (5 departments)
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    budget DECIMAL(15,2) DEFAULT 100000.00
);

INSERT INTO departments (name, code, budget)
VALUES
('IT', 'IT', 500000.00),
('HR', 'HR', 300000.00),
('Sales', 'SALES', 400000.00),
('Finance', 'FIN', 350000.00),
('Operations', 'OPS', 450000.00);

-- Employees (50 employees, safe department references)
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    salary DECIMAL(12,2) DEFAULT 50000.00,
    hire_date DATE DEFAULT CURRENT_DATE
);

INSERT INTO employees (employee_id, first_name, last_name, email, department_id, salary)
SELECT 
    'EMP' || LPAD(generate_series::text, 3, '0'),
    'First' || generate_series,
    'Last' || generate_series,
    'emp' || generate_series || '@company.com',
    ((generate_series - 1) % 5) + 1,   -- Safe department_id: 1-5
    (40000 + (generate_series * 1000))::decimal(12,2)
FROM generate_series(1, 50);

-- Payroll (150 records = 50 employees × 3 months)
CREATE TABLE payroll (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    pay_date DATE NOT NULL,
    gross_pay DECIMAL(12,2) NOT NULL,
    net_pay DECIMAL(12,2) NOT NULL
);

INSERT INTO payroll (employee_id, pay_date, gross_pay, net_pay)
SELECT 
    ((generate_series - 1) % 50) + 1,  -- Safe employee_id: 1-50
    CURRENT_DATE - (((generate_series - 1) / 50) * 30),
    4000.00,
    3000.00
FROM generate_series(1, 150);

CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_payroll_employee ON payroll(employee_id);

\echo 'HR system database created with safe data';

-- =============================================================================
-- FINAL STATISTICS GENERATION
-- =============================================================================
\c postgres

\echo 'Generating query statistics...';

-- Generate some query activity for pg_stat_statements
\c ecommerce
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM orders;

\c analytics
SELECT COUNT(*) FROM page_views;
SELECT COUNT(*) FROM sales_summary;

\c inventory
SELECT COUNT(*) FROM suppliers;
SELECT COUNT(*) FROM inventory_items;

\c hr_system
SELECT COUNT(*) FROM departments;
SELECT COUNT(*) FROM employees;

\c postgres

\echo '============================================================================='
\echo 'SIMPLE TEST DATA CREATION COMPLETED!'
\echo '============================================================================='
\echo 'Created databases:'
\echo '  - ecommerce: 5 categories, 50 products, 100 customers, 200 orders, 400 order_items'
\echo '  - analytics: 1000 page_views, 30 sales_summary records'  
\echo '  - inventory: 10 suppliers, 100 inventory_items, 50 purchase_orders'
\echo '  - hr_system: 5 departments, 50 employees, 150 payroll records'
\echo ''
\echo 'Created users:'
\echo '  - app_readonly (password: readonly123)'
\echo '  - app_readwrite (password: readwrite123)'
\echo '  - analytics_user (password: analytics123)'
\echo '  - backup_user (password: backup123)'
\echo ''
\echo 'Total records: ~2,095 across all databases'
\echo 'All foreign key references are SAFE - no constraint violations possible'
\echo '============================================================================='
