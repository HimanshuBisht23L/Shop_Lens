-- ============================================================
-- SHOPLENS DATABASE
-- MODERN PRODUCTION SCHEMA
-- ============================================================

BEGIN;

-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Immutable helper to allow array_to_string inside GENERATED ALWAYS AS tsvector
CREATE OR REPLACE FUNCTION immutable_array_to_string(arr text[], sep text) 
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT array_to_string(arr, sep);
$$;

-- Drop obsolete/legacy tables for clean initialization
DROP TABLE IF EXISTS sale_items CASCADE;
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS inventory_uploads CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS search_history CASCADE;
DROP TABLE IF EXISTS product_attributes CASCADE;
DROP TABLE IF EXISTS attributes CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS sub_categories CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- CATEGORIES & SUB-CATEGORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sub_categories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    synonyms TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_category_sub_category UNIQUE (category_id, name)
);

-- ============================================================
-- STORES
-- ============================================================

CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    address TEXT NOT NULL,
    phone VARCHAR(20),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    opening_time TIME,
    closing_time TIME,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL DEFAULT '',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sub_category_id INTEGER REFERENCES sub_categories(id) ON DELETE SET NULL,
    sub_category_name VARCHAR(100),
    description TEXT,
    net_quantity VARCHAR(50),
    image_url TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    specifications JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 384-d dense vector for BAAI/bge-small-en-v1.5
    embedding vector(384) NULL,

    -- Weighted Full-Text Search tsvector (Title: A, Brand: A, Sub-category & Tags: B, Description: C)
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(brand, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(sub_category_name, '')), 'B') ||
        setweight(to_tsvector('english', immutable_array_to_string(coalesce(tags, '{}'), ' ')), 'B') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'C')
    ) STORED,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INVENTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    price NUMERIC(10, 2) NOT NULL,
    mrp NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inventory_store_product UNIQUE (store_id, product_id),
    CONSTRAINT quantity_non_negative CHECK (quantity >= 0),
    CONSTRAINT price_non_negative CHECK (price >= 0)
);

-- ============================================================
-- SALES
-- ============================================================

CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    sold_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sale_total_non_negative CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    CONSTRAINT sale_item_quantity_positive CHECK (quantity > 0),
    CONSTRAINT sale_item_price_non_negative CHECK (unit_price >= 0),
    CONSTRAINT sale_item_subtotal_non_negative CHECK (subtotal >= 0)
);

-- ============================================================
-- INVENTORY UPLOADS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_uploads (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    total_records INTEGER NOT NULL DEFAULT 0,
    successful_records INTEGER NOT NULL DEFAULT 0,
    failed_records INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================
-- SEARCH HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- AI PREDICTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    predicted_quantity INTEGER NOT NULL,
    confidence NUMERIC(5, 2),
    prediction_date DATE NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT predicted_quantity_non_negative CHECK (predicted_quantity >= 0),
    CONSTRAINT confidence_valid CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 100))
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sub_category ON products(sub_category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_sub_category_name ON products(sub_category_name);
CREATE INDEX IF NOT EXISTS idx_products_search_vector ON products USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_tags ON products USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_stores_location ON stores USING gist(location);
CREATE INDEX IF NOT EXISTS idx_inventory_store ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_id);
CREATE INDEX IF NOT EXISTS idx_sales_sold_at ON sales(sold_at);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_store_product ON predictions(store_id, product_id);

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE users IS 'All ShopLens user accounts. A user can also own/manage a store.';
COMMENT ON TABLE stores IS 'Local stores registered on ShopLens.';
COMMENT ON TABLE categories IS '13 quick-commerce categories.';
COMMENT ON TABLE sub_categories IS '50 granular quick-commerce sub-categories with synonyms.';
COMMENT ON TABLE products IS 'Master catalog with brand, sub-category, tags, JSONB specs and BGE embeddings.';
COMMENT ON TABLE inventory IS 'Store-specific product quantity, MRP, price, and availability.';

COMMIT;
