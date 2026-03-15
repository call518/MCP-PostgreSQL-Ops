-- Test database initialization script
-- Runs on all PG versions (12-18) via docker-entrypoint-initdb.d

-- Enable pg_stat_statements (preloaded via shared_preload_libraries)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS inventory;

-- Sales schema tables
CREATE TABLE sales.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE sales.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES sales.customers(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sales.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES sales.orders(id),
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- Inventory schema tables
CREATE TABLE inventory.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inventory.stock_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES inventory.products(id),
    quantity_change INTEGER NOT NULL,
    movement_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add foreign key from order_items to products
ALTER TABLE sales.order_items
    ADD CONSTRAINT fk_order_items_product
    FOREIGN KEY (product_id) REFERENCES inventory.products(id);

-- Indexes
CREATE INDEX idx_orders_customer_id ON sales.orders(customer_id);
CREATE INDEX idx_orders_status ON sales.orders(status);
CREATE INDEX idx_orders_created_at ON sales.orders(created_at);
CREATE INDEX idx_order_items_order_id ON sales.order_items(order_id);
CREATE INDEX idx_order_items_product_id ON sales.order_items(product_id);
CREATE INDEX idx_products_category ON inventory.products(category);
CREATE INDEX idx_products_sku ON inventory.products(sku);
CREATE INDEX idx_stock_movements_product_id ON inventory.stock_movements(product_id);
CREATE INDEX idx_stock_movements_type ON inventory.stock_movements(movement_type);

-- Seed data: products
INSERT INTO inventory.products (name, sku, price, stock_quantity, category)
SELECT
    'Product ' || i,
    'SKU-' || LPAD(i::text, 5, '0'),
    (random() * 100 + 1)::numeric(10,2),
    (random() * 500)::integer,
    CASE (i % 5)
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Books'
        WHEN 2 THEN 'Clothing'
        WHEN 3 THEN 'Food'
        WHEN 4 THEN 'Tools'
    END
FROM generate_series(1, 20) AS i;

-- Seed data: customers
INSERT INTO sales.customers (name, email, status)
SELECT
    'Customer ' || i,
    'customer' || i || '@example.com',
    CASE WHEN random() > 0.2 THEN 'active' ELSE 'inactive' END
FROM generate_series(1, 20) AS i;

-- Seed data: orders
INSERT INTO sales.orders (customer_id, total_amount, status, created_at)
SELECT
    (random() * 19 + 1)::integer,
    (random() * 500 + 10)::numeric(10,2),
    CASE (i % 4)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'completed'
        WHEN 2 THEN 'shipped'
        WHEN 3 THEN 'cancelled'
    END,
    NOW() - (random() * 30 || ' days')::interval
FROM generate_series(1, 40) AS i;

-- Seed data: order items
INSERT INTO sales.order_items (order_id, product_id, quantity, unit_price)
SELECT
    (random() * 39 + 1)::integer,
    (random() * 19 + 1)::integer,
    (random() * 5 + 1)::integer,
    (random() * 100 + 1)::numeric(10,2)
FROM generate_series(1, 80) AS i;

-- Seed data: stock movements
INSERT INTO inventory.stock_movements (product_id, quantity_change, movement_type)
SELECT
    (random() * 19 + 1)::integer,
    CASE WHEN random() > 0.5 THEN (random() * 50 + 1)::integer ELSE -(random() * 20 + 1)::integer END,
    CASE (i % 3)
        WHEN 0 THEN 'receipt'
        WHEN 1 THEN 'sale'
        WHEN 2 THEN 'adjustment'
    END
FROM generate_series(1, 60) AS i;

-- Run ANALYZE to populate statistics
ANALYZE;

-- Run some queries to warm pg_stat_statements
SELECT count(*) FROM sales.customers WHERE status = 'active';
SELECT c.name, count(o.id) as order_count
FROM sales.customers c
LEFT JOIN sales.orders o ON o.customer_id = c.id
GROUP BY c.name;
SELECT p.name, p.stock_quantity, p.category
FROM inventory.products p
WHERE p.stock_quantity < 100
ORDER BY p.stock_quantity;
SELECT o.id, o.total_amount, c.name
FROM sales.orders o
JOIN sales.customers c ON c.id = o.customer_id
WHERE o.status = 'completed';
