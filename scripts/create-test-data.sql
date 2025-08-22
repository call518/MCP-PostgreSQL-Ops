-- PostgreSQL Test Data Generator
-- This script creates sample databases, tables, indexes, users, and data
-- for comprehensive testing of MCP PostgreSQL Operations Server

-- Enable extensions first
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- =============================================================================
-- CREATE TEST DATABASES
-- =============================================================================

-- E-commerce database
CREATE DATABASE ecommerce 
    WITH OWNER = postgres 
    ENCODING = 'UTF8' 
    LC_COLLATE = 'en_US.utf8' 
    LC_CTYPE = 'en_US.utf8';

-- Analytics database  
CREATE DATABASE analytics
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8';

-- Inventory management database
CREATE DATABASE inventory
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8';

-- HR database
CREATE DATABASE hr_system
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8';

-- =============================================================================
-- CREATE TEST USERS
-- =============================================================================

-- Application users
CREATE USER app_readonly WITH PASSWORD 'readonly123';
CREATE USER app_readwrite WITH PASSWORD 'readwrite123';
CREATE USER analytics_user WITH PASSWORD 'analytics123';
CREATE USER backup_user WITH PASSWORD 'backup123';

-- Grant database access
GRANT CONNECT ON DATABASE ecommerce TO app_readonly, app_readwrite;
GRANT CONNECT ON DATABASE analytics TO analytics_user;
GRANT CONNECT ON DATABASE inventory TO app_readwrite;
GRANT CONNECT ON DATABASE hr_system TO app_readwrite;

-- Grant schema permissions (will be applied after schema creation)
-- These will be applied in each database context below

\echo 'Basic databases and users created. Now creating tables and data...'

-- =============================================================================
-- ECOMMERCE DATABASE SCHEMA AND DATA
-- =============================================================================
\c ecommerce

-- Enable extensions in this database
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS customer_service;

-- Grant permissions
GRANT USAGE ON SCHEMA public, sales, inventory, customer_service TO app_readonly, app_readwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA public, sales, inventory, customer_service TO app_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public, sales, inventory, customer_service TO app_readwrite;

-- Categories table
CREATE TABLE public.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE public.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    sku VARCHAR(50) UNIQUE NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    weight_kg DECIMAL(8,3),
    dimensions_cm VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Customers table
CREATE TABLE public.customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0.00,
    customer_level VARCHAR(20) DEFAULT 'bronze'
);

-- Orders table
CREATE TABLE sales.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    subtotal DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50),
    shipping_address TEXT,
    billing_address TEXT,
    notes TEXT
);

-- Order items table
CREATE TABLE sales.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES sales.orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00
);

-- Reviews table
CREATE TABLE public.reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    customer_id INTEGER REFERENCES customers(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    review_text TEXT,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified_purchase BOOLEAN DEFAULT FALSE
);

-- Inventory movements
CREATE TABLE inventory.stock_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    movement_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity INTEGER NOT NULL,
    reference_number VARCHAR(100),
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Customer service tickets
CREATE TABLE customer_service.support_tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Create indexes for better performance testing
CREATE INDEX idx_products_category ON public.products(category_id);
CREATE INDEX idx_products_sku ON public.products(sku);
CREATE INDEX idx_products_price ON public.products(price);
CREATE INDEX idx_products_active ON public.products(is_active);
CREATE INDEX idx_customers_email ON public.customers(email);
CREATE INDEX idx_customers_registration ON public.customers(registration_date);
CREATE INDEX idx_customers_level ON public.customers(customer_level);
CREATE INDEX idx_orders_customer ON sales.orders(customer_id);
CREATE INDEX idx_orders_date ON sales.orders(order_date);
CREATE INDEX idx_orders_status ON sales.orders(status);
CREATE INDEX idx_orders_number ON sales.orders(order_number);
CREATE INDEX idx_order_items_order ON sales.order_items(order_id);
CREATE INDEX idx_order_items_product ON sales.order_items(product_id);
CREATE INDEX idx_reviews_product ON public.reviews(product_id);
CREATE INDEX idx_reviews_customer ON public.reviews(customer_id);
CREATE INDEX idx_reviews_rating ON public.reviews(rating);
CREATE INDEX idx_stock_movements_product ON inventory.stock_movements(product_id);
CREATE INDEX idx_stock_movements_date ON inventory.stock_movements(created_at);
CREATE INDEX idx_tickets_customer ON customer_service.support_tickets(customer_id);
CREATE INDEX idx_tickets_status ON customer_service.support_tickets(status);
CREATE INDEX idx_tickets_created ON customer_service.support_tickets(created_at);

-- Insert sample data
\echo 'Inserting ecommerce sample data...'

-- Categories
INSERT INTO public.categories (name, description, parent_id) VALUES
('Electronics', 'Electronic devices and accessories', NULL),
('Computers', 'Desktop and laptop computers', 1),
('Mobile Phones', 'Smartphones and accessories', 1),
('Home & Garden', 'Home improvement and garden supplies', NULL),
('Clothing', 'Apparel and fashion items', NULL),
('Books', 'Physical and digital books', NULL),
('Sports', 'Sports equipment and accessories', NULL),
('Automotive', 'Car parts and accessories', NULL);

-- Products (100 products)
INSERT INTO public.products (name, description, price, cost, category_id, sku, stock_quantity, weight_kg) 
SELECT 
    'Product ' || generate_series || ' - ' || c.name,
    'Description for product ' || generate_series || ' in category ' || c.name,
    (random() * 500 + 10)::decimal(10,2),
    (random() * 300 + 5)::decimal(10,2),
    c.id,
    'SKU' || LPAD(generate_series::text, 6, '0'),
    (random() * 100 + 1)::integer,
    (random() * 5 + 0.1)::decimal(8,3)
FROM generate_series(1, 100), categories c
WHERE generate_series % 8 = c.id - 1;

-- Customers (500 customers)
INSERT INTO public.customers (email, first_name, last_name, phone, date_of_birth, total_orders, total_spent, customer_level)
SELECT 
    'user' || generate_series || '@example.com',
    'FirstName' || generate_series,
    'LastName' || generate_series,
    '+1555' || LPAD((random() * 9999999)::integer::text, 7, '0'),
    CURRENT_DATE - INTERVAL '18 years' - (random() * INTERVAL '50 years'),
    (random() * 20)::integer,
    (random() * 2000)::decimal(12,2),
    CASE 
        WHEN random() < 0.6 THEN 'bronze'
        WHEN random() < 0.85 THEN 'silver'
        WHEN random() < 0.95 THEN 'gold'
        ELSE 'platinum'
    END
FROM generate_series(1, 500);

-- Orders (2000 orders)
INSERT INTO sales.orders (customer_id, order_number, order_date, status, subtotal, tax_amount, shipping_cost, total_amount, payment_method)
SELECT 
    (random() * 500 + 1)::integer,
    'ORD' || LPAD(generate_series::text, 8, '0'),
    CURRENT_TIMESTAMP - (random() * INTERVAL '365 days'),
    CASE (random() * 5)::integer
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'shipped'
        WHEN 3 THEN 'delivered'
        ELSE 'completed'
    END,
    (random() * 500 + 20)::decimal(12,2),
    (random() * 50 + 5)::decimal(12,2),
    (random() * 20 + 5)::decimal(10,2),
    (random() * 600 + 30)::decimal(12,2),
    CASE (random() * 4)::integer
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'paypal'
        WHEN 2 THEN 'bank_transfer'
        ELSE 'cash_on_delivery'
    END
FROM generate_series(1, 2000);

-- Order items (5000 items)
INSERT INTO sales.order_items (order_id, product_id, quantity, unit_price, total_price)
SELECT 
    (random() * 2000 + 1)::integer,
    (random() * 100 + 1)::integer,
    (random() * 5 + 1)::integer,
    p.price,
    p.price * (random() * 5 + 1)::integer
FROM generate_series(1, 5000), products p
WHERE (random() * 100 + 1)::integer = p.id
LIMIT 5000;

-- Reviews (1500 reviews)
INSERT INTO public.reviews (product_id, customer_id, rating, title, review_text, helpful_votes, is_verified_purchase)
SELECT 
    (random() * 100 + 1)::integer,
    (random() * 500 + 1)::integer,
    (random() * 5 + 1)::integer,
    'Review title ' || generate_series,
    'This is a sample review text for product testing. Review number ' || generate_series,
    (random() * 25)::integer,
    random() < 0.7
FROM generate_series(1, 1500);

-- Stock movements (3000 movements)
INSERT INTO inventory.stock_movements (product_id, movement_type, quantity, reference_number, reason)
SELECT 
    (random() * 100 + 1)::integer,
    CASE (random() * 3)::integer
        WHEN 0 THEN 'in'
        WHEN 1 THEN 'out'
        ELSE 'adjustment'
    END,
    (random() * 50 + 1)::integer,
    'REF' || LPAD(generate_series::text, 8, '0'),
    'Sample movement reason ' || generate_series
FROM generate_series(1, 3000);

-- Support tickets (800 tickets)
INSERT INTO customer_service.support_tickets (customer_id, ticket_number, subject, description, priority, status, assigned_to)
SELECT 
    (random() * 500 + 1)::integer,
    'TKT' || LPAD(generate_series::text, 8, '0'),
    'Support issue ' || generate_series,
    'This is a sample support ticket description for testing purposes. Ticket number ' || generate_series,
    CASE (random() * 3)::integer
        WHEN 0 THEN 'low'
        WHEN 1 THEN 'medium'
        ELSE 'high'
    END,
    CASE (random() * 4)::integer
        WHEN 0 THEN 'open'
        WHEN 1 THEN 'in_progress'
        WHEN 2 THEN 'resolved'
        ELSE 'closed'
    END,
    'Agent' || ((random() * 10 + 1)::integer)
FROM generate_series(1, 800);

\echo 'Ecommerce database populated successfully!'

-- =============================================================================
-- ANALYTICS DATABASE SCHEMA AND DATA
-- =============================================================================
\c analytics

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Web analytics table
CREATE TABLE public.page_views (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id INTEGER,
    page_url VARCHAR(500) NOT NULL,
    page_title VARCHAR(200),
    referrer VARCHAR(500),
    user_agent TEXT,
    ip_address INET,
    view_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_on_page INTEGER, -- seconds
    bounce BOOLEAN DEFAULT FALSE
);

-- Sales analytics
CREATE TABLE public.sales_summary (
    id SERIAL PRIMARY KEY,
    date_key DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0.00,
    total_customers INTEGER DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    avg_order_value DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product performance
CREATE TABLE public.product_analytics (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    date_key DATE NOT NULL,
    views INTEGER DEFAULT 0,
    cart_adds INTEGER DEFAULT 0,
    purchases INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0.00,
    conversion_rate DECIMAL(5,4) DEFAULT 0.0000
);

-- Create indexes
CREATE INDEX idx_page_views_timestamp ON public.page_views(view_timestamp);
CREATE INDEX idx_page_views_user ON public.page_views(user_id);
CREATE INDEX idx_page_views_session ON public.page_views(session_id);
CREATE INDEX idx_sales_summary_date ON public.sales_summary(date_key);
CREATE INDEX idx_product_analytics_product ON public.product_analytics(product_id);
CREATE INDEX idx_product_analytics_date ON public.product_analytics(date_key);

-- Insert analytics data
\echo 'Inserting analytics sample data...'

-- Page views (50000 records)
INSERT INTO public.page_views (session_id, user_id, page_url, page_title, referrer, user_agent, ip_address, view_timestamp, time_on_page, bounce)
SELECT 
    'sess_' || LPAD((generate_series / 10)::text, 10, '0'),
    CASE WHEN random() < 0.3 THEN NULL ELSE (random() * 500 + 1)::integer END,
    '/page/' || (random() * 100 + 1)::integer,
    'Page Title ' || (random() * 100 + 1)::integer,
    CASE WHEN random() < 0.4 THEN NULL ELSE 'https://google.com/search' END,
    'Mozilla/5.0 (compatible; TestBot/1.0)',
    ('192.168.1.' || (random() * 255)::integer)::inet,
    CURRENT_TIMESTAMP - (random() * INTERVAL '30 days'),
    (random() * 300 + 5)::integer,
    random() < 0.35
FROM generate_series(1, 50000);

-- Sales summary (90 days)
INSERT INTO public.sales_summary (date_key, total_orders, total_revenue, total_customers, new_customers, avg_order_value)
SELECT 
    CURRENT_DATE - generate_series,
    (random() * 100 + 10)::integer,
    (random() * 50000 + 1000)::decimal(15,2),
    (random() * 80 + 5)::integer,
    (random() * 20 + 1)::integer,
    (random() * 200 + 50)::decimal(10,2)
FROM generate_series(0, 89);

-- Product analytics (9000 records = 100 products × 90 days)
INSERT INTO public.product_analytics (product_id, date_key, views, cart_adds, purchases, revenue, conversion_rate)
SELECT 
    (series.generate_series % 100) + 1,
    CURRENT_DATE - (series.generate_series / 100),
    (random() * 500 + 10)::integer,
    (random() * 50 + 1)::integer,
    (random() * 10 + 1)::integer,
    (random() * 1000 + 50)::decimal(12,2),
    (random() * 0.1)::decimal(5,4)
FROM generate_series(0, 8999) AS series;

\echo 'Analytics database populated successfully!'

-- =============================================================================
-- INVENTORY DATABASE SCHEMA AND DATA
-- =============================================================================
\c inventory

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO app_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;

-- Warehouses
CREATE TABLE public.warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'USA',
    postal_code VARCHAR(20),
    manager_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    capacity INTEGER, -- max items
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers
CREATE TABLE public.suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    payment_terms VARCHAR(50),
    rating DECIMAL(3,2), -- 0.00 to 5.00
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory items
CREATE TABLE public.inventory_items (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    supplier_id INTEGER REFERENCES suppliers(id),
    unit_cost DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    reorder_level INTEGER DEFAULT 10,
    max_stock_level INTEGER DEFAULT 100,
    weight_kg DECIMAL(8,3),
    dimensions VARCHAR(50),
    category VARCHAR(100),
    location_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock levels per warehouse
CREATE TABLE public.stock_levels (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES inventory_items(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    quantity_on_hand INTEGER DEFAULT 0,
    quantity_reserved INTEGER DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    last_counted TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, warehouse_id)
);

-- Purchase orders
CREATE TABLE public.purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    order_date DATE DEFAULT CURRENT_DATE,
    expected_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(15,2),
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_inventory_items_sku ON public.inventory_items(sku);
CREATE INDEX idx_inventory_items_supplier ON public.inventory_items(supplier_id);
CREATE INDEX idx_inventory_items_category ON public.inventory_items(category);
CREATE INDEX idx_stock_levels_item ON public.stock_levels(item_id);
CREATE INDEX idx_stock_levels_warehouse ON public.stock_levels(warehouse_id);
CREATE INDEX idx_stock_levels_available ON public.stock_levels(quantity_available);
CREATE INDEX idx_purchase_orders_supplier ON public.purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON public.purchase_orders(status);
CREATE INDEX idx_purchase_orders_date ON public.purchase_orders(order_date);

-- Insert inventory data
\echo 'Inserting inventory sample data...'

-- Warehouses (5 warehouses)
INSERT INTO public.warehouses (name, code, address, city, state, country, postal_code, manager_name, phone, email, capacity)
VALUES
('Main Distribution Center', 'MDC', '123 Industrial Blvd', 'Los Angeles', 'CA', 'USA', '90210', 'John Smith', '+1-555-0101', 'john@warehouse.com', 10000),
('East Coast Warehouse', 'ECW', '456 Harbor St', 'New York', 'NY', 'USA', '10001', 'Jane Doe', '+1-555-0102', 'jane@warehouse.com', 7500),
('Midwest Hub', 'MWH', '789 Central Ave', 'Chicago', 'IL', 'USA', '60601', 'Bob Johnson', '+1-555-0103', 'bob@warehouse.com', 8000),
('Texas Facility', 'TXF', '321 Oil Rd', 'Houston', 'TX', 'USA', '77001', 'Alice Brown', '+1-555-0104', 'alice@warehouse.com', 6000),
('Pacific Northwest', 'PNW', '654 Forest Dr', 'Seattle', 'WA', 'USA', '98101', 'Charlie Wilson', '+1-555-0105', 'charlie@warehouse.com', 5500);

-- Suppliers (20 suppliers)
INSERT INTO public.suppliers (name, code, contact_person, email, phone, address, payment_terms, rating, is_active)
SELECT 
    'Supplier Company ' || generate_series,
    'SUP' || LPAD(generate_series::text, 3, '0'),
    'Contact Person ' || generate_series,
    'supplier' || generate_series || '@company.com',
    '+1-555-' || LPAD((1000 + generate_series)::text, 4, '0'),
    generate_series || ' Business Park, Suite ' || (generate_series * 10),
    CASE (generate_series % 3)
        WHEN 0 THEN 'Net 30'
        WHEN 1 THEN 'Net 60'
        ELSE '2/10 Net 30'
    END,
    (random() * 2 + 3)::decimal(3,2), -- 3.00 to 5.00
    generate_series <= 18 -- 2 inactive suppliers
FROM generate_series(1, 20);

-- Inventory items (500 items)
INSERT INTO public.inventory_items (sku, name, description, supplier_id, unit_cost, selling_price, reorder_level, max_stock_level, weight_kg, category, location_code)
SELECT 
    'INV' || LPAD(generate_series::text, 6, '0'),
    'Inventory Item ' || generate_series,
    'Description for inventory item ' || generate_series,
    (random() * 20 + 1)::integer,
    (random() * 100 + 5)::decimal(10,2),
    (random() * 200 + 10)::decimal(10,2),
    (random() * 20 + 5)::integer,
    (random() * 200 + 50)::integer,
    (random() * 10 + 0.1)::decimal(8,3),
    CASE (random() * 8)::integer
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Automotive'
        WHEN 2 THEN 'Home & Garden'
        WHEN 3 THEN 'Sports'
        WHEN 4 THEN 'Clothing'
        WHEN 5 THEN 'Books'
        WHEN 6 THEN 'Tools'
        ELSE 'General'
    END,
    'LOC-' || LPAD((random() * 999 + 1)::integer::text, 3, '0')
FROM generate_series(1, 500);

-- Stock levels (2500 records = 500 items × 5 warehouses)
INSERT INTO public.stock_levels (item_id, warehouse_id, quantity_on_hand, quantity_reserved, last_counted, last_updated)
SELECT 
    ((generate_series - 1) % 500) + 1,
    ((generate_series - 1) / 500) + 1,
    (random() * 100 + 1)::integer,
    (random() * 20)::integer,
    CURRENT_TIMESTAMP - (random() * INTERVAL '30 days'),
    CURRENT_TIMESTAMP - (random() * INTERVAL '7 days')
FROM generate_series(1, 2500);

-- Purchase orders (200 orders)
INSERT INTO public.purchase_orders (po_number, supplier_id, warehouse_id, order_date, expected_date, status, total_amount, notes, created_by)
SELECT 
    'PO' || LPAD(generate_series::text, 6, '0'),
    (random() * 20 + 1)::integer,
    (random() * 5 + 1)::integer,
    CURRENT_DATE - (random() * 90)::integer,
    CURRENT_DATE + (random() * 30)::integer,
    CASE (random() * 5)::integer
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'approved'
        WHEN 2 THEN 'sent'
        WHEN 3 THEN 'received'
        ELSE 'completed'
    END,
    (random() * 10000 + 500)::decimal(15,2),
    'Sample purchase order notes ' || generate_series,
    'Buyer' || ((random() * 5 + 1)::integer)
FROM generate_series(1, 200);

\echo 'Inventory database populated successfully!'

-- =============================================================================
-- HR SYSTEM DATABASE SCHEMA AND DATA
-- =============================================================================
\c hr_system

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO app_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;

-- Departments
CREATE TABLE public.departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    description TEXT,
    manager_id INTEGER,
    budget DECIMAL(15,2),
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees
CREATE TABLE public.employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    manager_id INTEGER REFERENCES employees(id),
    salary DECIMAL(12,2),
    employment_status VARCHAR(20) DEFAULT 'active',
    date_of_birth DATE,
    address TEXT,
    emergency_contact VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add manager foreign key to departments (circular reference)
ALTER TABLE public.departments ADD CONSTRAINT fk_dept_manager 
    FOREIGN KEY (manager_id) REFERENCES employees(id);

-- Payroll records
CREATE TABLE public.payroll (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    gross_pay DECIMAL(12,2) NOT NULL,
    tax_deductions DECIMAL(12,2) NOT NULL,
    other_deductions DECIMAL(12,2) DEFAULT 0.00,
    net_pay DECIMAL(12,2) NOT NULL,
    overtime_hours DECIMAL(5,2) DEFAULT 0.00,
    overtime_pay DECIMAL(10,2) DEFAULT 0.00,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time tracking
CREATE TABLE public.time_entries (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    work_date DATE NOT NULL,
    clock_in TIME,
    clock_out TIME,
    break_minutes INTEGER DEFAULT 0,
    total_hours DECIMAL(4,2),
    project_code VARCHAR(50),
    notes TEXT,
    approved_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance reviews
CREATE TABLE public.performance_reviews (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    reviewer_id INTEGER REFERENCES employees(id),
    review_period_start DATE NOT NULL,
    review_period_end DATE NOT NULL,
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    goals_achievement INTEGER CHECK (goals_achievement >= 1 AND goals_achievement <= 5),
    communication_skills INTEGER CHECK (communication_skills >= 1 AND communication_skills <= 5),
    technical_skills INTEGER CHECK (technical_skills >= 1 AND technical_skills <= 5),
    teamwork INTEGER CHECK (teamwork >= 1 AND teamwork <= 5),
    comments TEXT,
    improvement_areas TEXT,
    goals_next_period TEXT,
    review_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_employees_department ON public.employees(department_id);
CREATE INDEX idx_employees_manager ON public.employees(manager_id);
CREATE INDEX idx_employees_status ON public.employees(employment_status);
CREATE INDEX idx_employees_hire_date ON public.employees(hire_date);
CREATE INDEX idx_payroll_employee ON public.payroll(employee_id);
CREATE INDEX idx_payroll_period ON public.payroll(pay_period_start, pay_period_end);
CREATE INDEX idx_time_entries_employee ON public.time_entries(employee_id);
CREATE INDEX idx_time_entries_date ON public.time_entries(work_date);
CREATE INDEX idx_performance_reviews_employee ON public.performance_reviews(employee_id);
CREATE INDEX idx_performance_reviews_reviewer ON public.performance_reviews(reviewer_id);

-- Insert HR data
\echo 'Inserting HR system sample data...'

-- Departments (8 departments)
INSERT INTO public.departments (name, code, description, budget, location)
VALUES
('Human Resources', 'HR', 'Human resources and talent management', 500000.00, 'Building A, Floor 1'),
('Information Technology', 'IT', 'Technology infrastructure and development', 2000000.00, 'Building B, Floor 3'),
('Sales', 'SALES', 'Sales and business development', 1500000.00, 'Building A, Floor 2'),
('Marketing', 'MKT', 'Marketing and brand management', 800000.00, 'Building A, Floor 2'),
('Finance', 'FIN', 'Financial planning and accounting', 600000.00, 'Building C, Floor 1'),
('Operations', 'OPS', 'Operations and logistics', 1200000.00, 'Building D, Floor 1'),
('Customer Service', 'CS', 'Customer support and relations', 400000.00, 'Building A, Floor 1'),
('Research & Development', 'RD', 'Product research and development', 3000000.00, 'Building E, Floor 2');

-- Employees (150 employees)
INSERT INTO public.employees (employee_id, first_name, last_name, email, phone, hire_date, job_title, department_id, salary, employment_status, date_of_birth, address)
SELECT 
    'EMP' || LPAD(generate_series::text, 4, '0'),
    'FirstName' || generate_series,
    'LastName' || generate_series,
    'employee' || generate_series || '@company.com',
    '+1-555-' || LPAD((2000 + generate_series)::text, 4, '0'),
    CURRENT_DATE - (random() * 2000 + 365)::integer, -- 1-6 years ago
    CASE (random() * 12)::integer
        WHEN 0 THEN 'Software Engineer'
        WHEN 1 THEN 'Senior Developer'
        WHEN 2 THEN 'Project Manager'
        WHEN 3 THEN 'Sales Representative'
        WHEN 4 THEN 'Marketing Specialist'
        WHEN 5 THEN 'Account Manager'
        WHEN 6 THEN 'HR Generalist'
        WHEN 7 THEN 'Financial Analyst'
        WHEN 8 THEN 'Operations Coordinator'
        WHEN 9 THEN 'Customer Support Agent'
        WHEN 10 THEN 'Research Analyst'
        ELSE 'Administrative Assistant'
    END,
    (random() * 8 + 1)::integer,
    (random() * 80000 + 40000)::decimal(12,2), -- $40K - $120K
    CASE WHEN random() < 0.95 THEN 'active' ELSE 'inactive' END,
    CURRENT_DATE - INTERVAL '25 years' - (random() * INTERVAL '20 years'),
    generate_series || ' Employee Street, City, State 12345'
FROM generate_series(1, 150);

-- Update some employees to be managers
UPDATE public.employees SET manager_id = CASE 
    WHEN id % 10 = 1 THEN NULL -- Top managers
    ELSE ((id-1) / 10) * 10 + 1 -- Every 10th employee is a manager
END;

-- Update departments with managers
UPDATE public.departments SET manager_id = d.emp_id
FROM (
    SELECT id as dept_id, 
           (SELECT e.id FROM employees e WHERE e.department_id = departments.id ORDER BY hire_date LIMIT 1) as emp_id
    FROM departments
) d
WHERE id = d.dept_id;

-- Payroll records (1800 records = 150 employees × 12 months)
INSERT INTO public.payroll (employee_id, pay_period_start, pay_period_end, gross_pay, tax_deductions, other_deductions, net_pay, overtime_hours, overtime_pay)
SELECT 
    ((generate_series - 1) % 150) + 1,
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' * ((generate_series - 1) / 150),
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' * ((generate_series - 1) / 150) + INTERVAL '1 month' - INTERVAL '1 day',
    (e.salary / 12)::decimal(12,2),
    (e.salary / 12 * 0.25)::decimal(12,2), -- 25% tax rate
    (e.salary / 12 * 0.05)::decimal(12,2), -- 5% other deductions
    (e.salary / 12 * 0.70)::decimal(12,2), -- 70% net pay
    (random() * 10)::decimal(5,2),
    (random() * 500)::decimal(10,2)
FROM generate_series(1, 1800), employees e
WHERE e.id = ((generate_series - 1) % 150) + 1;

-- Time entries (10000 records)
INSERT INTO public.time_entries (employee_id, work_date, clock_in, clock_out, break_minutes, total_hours, project_code)
SELECT 
    (random() * 150 + 1)::integer,
    CURRENT_DATE - (random() * 90)::integer,
    ('08:00:00'::time + (random() * INTERVAL '2 hours'))::time,
    ('17:00:00'::time + (random() * INTERVAL '3 hours'))::time,
    (random() * 60 + 30)::integer, -- 30-90 minute breaks
    (random() * 3 + 7)::decimal(4,2), -- 7-10 hours
    'PROJ' || LPAD((random() * 20 + 1)::integer::text, 3, '0')
FROM generate_series(1, 10000);

-- Performance reviews (300 reviews = 150 employees × 2 years)
INSERT INTO public.performance_reviews (employee_id, reviewer_id, review_period_start, review_period_end, overall_rating, goals_achievement, communication_skills, technical_skills, teamwork, comments)
SELECT 
    generate_series,
    CASE WHEN e.manager_id IS NOT NULL THEN e.manager_id ELSE 1 END,
    CURRENT_DATE - INTERVAL '1 year' - INTERVAL '6 months' * ((generate_series - 1) / 150),
    CURRENT_DATE - INTERVAL '6 months' * ((generate_series - 1) / 150),
    (random() * 2 + 3)::integer, -- 3-5 rating
    (random() * 2 + 3)::integer,
    (random() * 2 + 3)::integer,
    (random() * 2 + 3)::integer,
    (random() * 2 + 3)::integer,
    'Performance review comments for employee ' || generate_series
FROM generate_series(1, 300), employees e
WHERE e.id = CASE WHEN generate_series <= 150 THEN generate_series ELSE generate_series - 150 END;

\echo 'HR system database populated successfully!'

-- =============================================================================
-- FINAL STEPS - Generate some query activity for pg_stat_statements
-- =============================================================================
\c postgres

\echo 'Generating query activity for performance statistics...'

-- Run some queries to populate pg_stat_statements
SELECT COUNT(*) FROM pg_database;
SELECT COUNT(*) FROM pg_user;

\c ecommerce
SELECT COUNT(*) FROM public.products;
SELECT COUNT(*) FROM public.customers; 
SELECT COUNT(*) FROM sales.orders;
SELECT p.name, COUNT(r.id) as review_count FROM public.products p LEFT JOIN public.reviews r ON p.id = r.product_id GROUP BY p.id, p.name ORDER BY review_count DESC LIMIT 10;
SELECT c.customer_level, COUNT(*), AVG(total_spent) FROM public.customers c GROUP BY c.customer_level;

\c analytics  
SELECT COUNT(*) FROM public.page_views;
SELECT COUNT(*) FROM public.sales_summary;

\c inventory
SELECT COUNT(*) FROM public.inventory_items;
SELECT COUNT(*) FROM public.stock_levels;
SELECT s.name, COUNT(i.id) FROM public.suppliers s LEFT JOIN public.inventory_items i ON s.id = i.supplier_id GROUP BY s.id, s.name;

\c hr_system
SELECT COUNT(*) FROM public.employees;
SELECT COUNT(*) FROM public.payroll;
SELECT d.name, COUNT(e.id) FROM public.departments d LEFT JOIN public.employees e ON d.id = e.department_id GROUP BY d.id, d.name;

\c postgres

\echo ''
\echo '============================================================================='
\echo 'TEST DATA GENERATION COMPLETED SUCCESSFULLY!'
\echo '============================================================================='
\echo ''
\echo 'Created test databases:'
\echo '  - ecommerce (with sales, inventory, customer_service schemas)'
\echo '  - analytics (web analytics and sales data)'  
\echo '  - inventory (warehouse and supplier management)'
\echo '  - hr_system (employee and payroll data)'
\echo ''
\echo 'Created test users:'
\echo '  - app_readonly (password: readonly123)'
\echo '  - app_readwrite (password: readwrite123)'
\echo '  - analytics_user (password: analytics123)'
\echo '  - backup_user (password: backup123)'
\echo ''
\echo 'Data volumes:'
\echo '  - ecommerce: ~9,000 records across 8 tables'
\echo '  - analytics: ~59,000 records across 3 tables' 
\echo '  - inventory: ~3,200 records across 5 tables'
\echo '  - hr_system: ~12,000+ records across 5 tables'
\echo '  - Total: ~83,000+ test records'
\echo ''
\echo 'All tables have appropriate indexes for performance testing.'
\echo 'Query activity has been generated for pg_stat_statements analysis.'
\echo ''
\echo 'You can now test all MCP PostgreSQL Operations Server tools with:'
\echo '  - Multi-database operations (database_name parameter)'
\echo '  - Performance monitoring (slow queries, index usage)'
\echo '  - Capacity analysis (database/table sizes)'
\echo '  - Configuration analysis'
\echo '  - User and permission management'
\echo ''
\echo 'Example test commands:'
\echo '  get_database_list()'
\echo '  get_table_list(database_name="ecommerce")'
\echo '  get_pg_stat_statements_top_queries(limit=10, database_name="ecommerce")'
\echo '  get_index_usage_stats(database_name="inventory")'
\echo '============================================================================='

-- =============================================================================
-- GENERATE STATISTICS DATA FOR NEW MCP TOOLS
-- =============================================================================
\echo ''
\echo 'Generating statistics data for new MCP tools...'

-- Generate I/O activity by scanning tables multiple times
\c ecommerce
\echo 'Generating I/O activity in ecommerce database...'
SELECT COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id;
SELECT COUNT(*) FROM orders o JOIN customers cu ON o.customer_id = cu.id;
SELECT COUNT(*) FROM order_items oi JOIN products p ON oi.product_id = p.id;

-- Force some index usage
SELECT * FROM products WHERE sku LIKE 'PROD-1%' ORDER BY price DESC;
SELECT * FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' ORDER BY created_at DESC;
SELECT * FROM customers WHERE email LIKE '%@example.com' ORDER BY last_name;

\c analytics
\echo 'Generating I/O activity in analytics database...'
SELECT COUNT(*) FROM sales_data WHERE sale_date >= CURRENT_DATE - INTERVAL '7 days';
SELECT COUNT(*) FROM web_analytics WHERE visit_date >= CURRENT_DATE - INTERVAL '30 days';
SELECT AVG(revenue) FROM sales_data WHERE sale_date >= CURRENT_DATE - INTERVAL '90 days';

\c inventory
\echo 'Generating I/O activity in inventory database...'
SELECT COUNT(*) FROM warehouse_items wi JOIN warehouses w ON wi.warehouse_id = w.id;
SELECT COUNT(*) FROM stock_movements WHERE movement_date >= CURRENT_DATE - INTERVAL '7 days';
SELECT * FROM suppliers ORDER BY name;

\c hr_system
\echo 'Generating I/O activity in hr_system database...'
SELECT COUNT(*) FROM employees e JOIN departments d ON e.department_id = d.id;
SELECT COUNT(*) FROM payroll_records WHERE pay_date >= CURRENT_DATE - INTERVAL '30 days';
SELECT * FROM employees WHERE hire_date >= CURRENT_DATE - INTERVAL '365 days';

-- Create some user-defined functions for function stats
\c ecommerce
\echo 'Creating user-defined functions for testing...'
CREATE OR REPLACE FUNCTION calculate_order_total(order_id INTEGER)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    total DECIMAL(10,2);
BEGIN
    SELECT SUM(quantity * unit_price) INTO total
    FROM order_items 
    WHERE order_items.order_id = $1;
    RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_customer_order_count(customer_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO order_count
    FROM orders
    WHERE orders.customer_id = $1;
    RETURN COALESCE(order_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Execute functions multiple times to generate statistics
\echo 'Executing functions to generate statistics...'
SELECT calculate_order_total(id) FROM orders LIMIT 20;
SELECT get_customer_order_count(id) FROM customers LIMIT 15;
SELECT calculate_order_total(id) FROM orders WHERE id BETWEEN 1 AND 10;
SELECT get_customer_order_count(id) FROM customers WHERE id BETWEEN 1 AND 5;

-- Force statistics collection
SELECT pg_stat_reset();

-- Run more queries to regenerate fresh statistics
\c ecommerce
SELECT COUNT(*) FROM products WHERE price > 100;
SELECT COUNT(*) FROM orders WHERE status = 'completed';
VACUUM ANALYZE products;
VACUUM ANALYZE orders;

\c analytics
SELECT COUNT(*) FROM sales_data;
VACUUM ANALYZE sales_data;

\c inventory  
SELECT COUNT(*) FROM warehouse_items;
VACUUM ANALYZE warehouse_items;

\c hr_system
SELECT COUNT(*) FROM employees;
VACUUM ANALYZE employees;

-- Re-execute functions after reset
\c ecommerce
SELECT calculate_order_total(id) FROM orders LIMIT 5;
SELECT get_customer_order_count(id) FROM customers LIMIT 5;

\echo ''
\echo 'Statistics data generation completed!'
\echo 'The following new MCP tools should now return data:'
\echo '  - get_database_stats() - Database performance metrics'
\echo '  - get_bgwriter_stats() - Background writer statistics' 
\echo '  - get_all_tables_stats() - Comprehensive table statistics'
\echo '  - get_user_functions_stats() - User-defined function performance'
\echo '  - get_table_io_stats() - Table I/O performance statistics'
\echo '  - get_index_io_stats() - Index I/O performance statistics'
\echo '  - get_database_conflicts_stats() - Replication conflict statistics'
\echo ''
