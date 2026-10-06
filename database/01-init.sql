-- ============================================================
-- SHOPLENS DATABASE
-- INITIAL SCHEMA
-- ============================================================

BEGIN;


-- ============================================================
-- EXTENSIONS
-- ============================================================

-- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Geospatial / location support
CREATE EXTENSION IF NOT EXISTS postgis;


-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- CATEGORIES
-- ============================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- STORES
-- ============================================================

CREATE TABLE stores (
    id SERIAL PRIMARY KEY,

    owner_id INTEGER NOT NULL,

    name VARCHAR(150) NOT NULL,

    description TEXT,

    address TEXT NOT NULL,

    phone VARCHAR(20),

    -- Latitude/Longitude location
    location GEOGRAPHY(POINT, 4326) NOT NULL,

    opening_time TIME,

    closing_time TIME,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_store_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- ============================================================
-- PRODUCTS
-- MASTER PRODUCT CATALOG
-- ============================================================

CREATE TABLE products (
    id SERIAL PRIMARY KEY,

    name VARCHAR(200) NOT NULL,

    normalized_name VARCHAR(200),

    description TEXT,

    category_id INTEGER,

    image_url TEXT,

    -- Semantic-search embedding will be added later
    -- when pgvector is installed.

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE SET NULL
);


-- ============================================================
-- INVENTORY
-- STORE <-> PRODUCT
-- ============================================================

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,

    store_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    quantity INTEGER NOT NULL DEFAULT 0,

    price NUMERIC(10, 2) NOT NULL,

    is_available BOOLEAN NOT NULL DEFAULT TRUE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_inventory_store
        FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_store_product
        UNIQUE (store_id, product_id),

    CONSTRAINT quantity_non_negative
        CHECK (quantity >= 0),

    CONSTRAINT price_non_negative
        CHECK (price >= 0)
);


-- ============================================================
-- SALES
-- ============================================================

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,

    store_id INTEGER NOT NULL,

    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,

    sold_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_sale_store
        FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE CASCADE,

    CONSTRAINT sale_total_non_negative
        CHECK (total_amount >= 0)
);


-- ============================================================
-- SALE ITEMS
-- ============================================================

CREATE TABLE sale_items (
    id SERIAL PRIMARY KEY,

    sale_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    quantity INTEGER NOT NULL,

    unit_price NUMERIC(10, 2) NOT NULL,

    subtotal NUMERIC(12, 2) NOT NULL,

    CONSTRAINT fk_sale_item_sale
        FOREIGN KEY (sale_id)
        REFERENCES sales(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_sale_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE RESTRICT,

    CONSTRAINT sale_item_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT sale_item_price_non_negative
        CHECK (unit_price >= 0),

    CONSTRAINT sale_item_subtotal_non_negative
        CHECK (subtotal >= 0)
);


-- ============================================================
-- INVENTORY UPLOADS
-- ============================================================

CREATE TABLE inventory_uploads (
    id SERIAL PRIMARY KEY,

    store_id INTEGER NOT NULL,

    file_name VARCHAR(255) NOT NULL,

    file_type VARCHAR(20) NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'pending',

    total_records INTEGER NOT NULL DEFAULT 0,

    successful_records INTEGER NOT NULL DEFAULT 0,

    failed_records INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CONSTRAINT fk_upload_store
        FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE CASCADE
);


-- ============================================================
-- SEARCH HISTORY
-- ============================================================

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,

    user_id INTEGER,

    query TEXT NOT NULL,

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_search_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);


-- ============================================================
-- AI / DEMAND PREDICTIONS
-- ============================================================

CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,

    store_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    predicted_quantity INTEGER NOT NULL,

    confidence NUMERIC(5, 2),

    prediction_date DATE NOT NULL,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_prediction_store
        FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_prediction_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    CONSTRAINT predicted_quantity_non_negative
        CHECK (predicted_quantity >= 0),

    CONSTRAINT confidence_valid
        CHECK (
            confidence IS NULL
            OR confidence BETWEEN 0 AND 100
        )
);


-- ============================================================
-- INDEXES
-- ============================================================


-- ------------------------------------------------------------
-- PostGIS location index
-- ------------------------------------------------------------

CREATE INDEX idx_stores_location
ON stores
USING GIST (location);


-- ------------------------------------------------------------
-- pg_trgm fuzzy search indexes
-- ------------------------------------------------------------

CREATE INDEX idx_products_name_trgm
ON products
USING GIN (name gin_trgm_ops);


CREATE INDEX idx_products_normalized_name_trgm
ON products
USING GIN (normalized_name gin_trgm_ops);


-- ------------------------------------------------------------
-- Foreign-key / lookup indexes
-- ------------------------------------------------------------

CREATE INDEX idx_products_category
ON products(category_id);


CREATE INDEX idx_inventory_store
ON inventory(store_id);


CREATE INDEX idx_inventory_product
ON inventory(product_id);


CREATE INDEX idx_sales_store
ON sales(store_id);


CREATE INDEX idx_sales_sold_at
ON sales(sold_at);


CREATE INDEX idx_sale_items_sale
ON sale_items(sale_id);


CREATE INDEX idx_sale_items_product
ON sale_items(product_id);


CREATE INDEX idx_search_history_user
ON search_history(user_id);


CREATE INDEX idx_search_history_created
ON search_history(created_at);


CREATE INDEX idx_predictions_store_product
ON predictions(store_id, product_id);


-- ============================================================
-- TABLE COMMENTS
-- ============================================================

COMMENT ON TABLE users IS
'All ShopLens user accounts. A user can also own/manage a store.';

COMMENT ON TABLE stores IS
'Local stores registered on ShopLens.';

COMMENT ON TABLE products IS
'Master product catalog shared across stores.';

COMMENT ON TABLE inventory IS
'Store-specific product quantity and price.';


-- ============================================================
-- FINISH
-- ============================================================

COMMIT;


SELECT 'ShopLens database schema created successfully.' AS message;