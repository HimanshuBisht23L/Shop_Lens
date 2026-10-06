-- ============================================================
-- SHOPLENS DEMO DATA
-- ============================================================

BEGIN;


-- ============================================================
-- USERS
-- ============================================================

INSERT INTO users
(full_name, email, password_hash)
VALUES
('Raj Sharma', 'raj@shoplens.demo', 'DEMO_PASSWORD_HASH_1'),
('Aman Verma', 'aman@shoplens.demo', 'DEMO_PASSWORD_HASH_2'),
('Priya Singh', 'priya@shoplens.demo', 'DEMO_PASSWORD_HASH_3'),
('Neha Gupta', 'neha@shoplens.demo', 'DEMO_PASSWORD_HASH_4'),
('Arjun Mehta', 'arjun@shoplens.demo', 'DEMO_PASSWORD_HASH_5');


-- ============================================================
-- CATEGORIES
-- ============================================================

INSERT INTO categories
(name, description)
VALUES
('Dairy', 'Milk, cheese, butter and other dairy products'),
('Bakery', 'Bread, cakes, buns and bakery products'),
('Snacks', 'Chips, biscuits, chocolates and snack items'),
('Beverages', 'Cold drinks, juices, tea and coffee'),
('Fruits', 'Fresh fruits'),
('Vegetables', 'Fresh vegetables'),
('Personal Care', 'Personal hygiene and personal care products'),
('Household', 'Cleaning and household products');


-- ============================================================
-- STORES
-- Coordinates are demo locations around Dehradun.
-- ST_MakePoint(longitude, latitude)
-- ============================================================

INSERT INTO stores
(
    owner_id,
    name,
    description,
    address,
    phone,
    location,
    opening_time,
    closing_time,
    is_active
)
VALUES

(
    1,
    'Sharma General Store',
    'Local grocery and daily essentials store',
    'Rajpur Road, Dehradun',
    '9876500001',
    ST_SetSRID(
        ST_MakePoint(78.0322, 30.3256),
        4326
    )::geography,
    '08:00',
    '21:00',
    TRUE
),

(
    2,
    'FreshMart',
    'Fresh groceries and household essentials',
    'Jakhan, Dehradun',
    '9876500002',
    ST_SetSRID(
        ST_MakePoint(78.0550, 30.3475),
        4326
    )::geography,
    '07:30',
    '22:00',
    TRUE
),

(
    3,
    'Gupta Grocery',
    'Neighborhood grocery store',
    'Ballupur, Dehradun',
    '9876500003',
    ST_SetSRID(
        ST_MakePoint(78.0045, 30.3310),
        4326
    )::geography,
    '08:00',
    '21:30',
    TRUE
),

(
    4,
    'City Supermarket',
    'Supermarket with groceries and daily essentials',
    'Clock Tower, Dehradun',
    '9876500004',
    ST_SetSRID(
        ST_MakePoint(78.0322, 30.3165),
        4326
    )::geography,
    '09:00',
    '22:00',
    TRUE
),

(
    5,
    'Local Needs Store',
    'Convenience store for everyday products',
    'Vasant Vihar, Dehradun',
    '9876500005',
    ST_SetSRID(
        ST_MakePoint(77.9975, 30.3160),
        4326
    )::geography,
    '08:30',
    '21:00',
    TRUE
);


-- ============================================================
-- PRODUCTS
-- ============================================================

INSERT INTO products
(
    name,
    normalized_name,
    description,
    category_id
)
VALUES

(
    'Cadbury Dairy Milk Chocolate',
    'cadbury dairy milk chocolate',
    'Milk chocolate bar',
    3
),

(
    'Cadbury 5 Star',
    'cadbury 5 star',
    'Caramel chocolate bar',
    3
),

(
    'Amul Taaza Milk',
    'amul taaza milk',
    'Fresh toned milk',
    1
),

(
    'Amul Butter',
    'amul butter',
    'Pasteurized table butter',
    1
),

(
    'Britannia Bread',
    'britannia bread',
    'Fresh white bread',
    2
),

(
    'Harvest Brown Bread',
    'harvest brown bread',
    'Whole wheat brown bread',
    2
),

(
    'Parle-G Biscuits',
    'parle g biscuits',
    'Classic glucose biscuits',
    3
),

(
    'Oreo Biscuits',
    'oreo biscuits',
    'Chocolate sandwich biscuits',
    3
),

(
    'Lays Classic Salted',
    'lays classic salted',
    'Classic salted potato chips',
    3
),

(
    'Kurkure Masala Munch',
    'kurkure masala munch',
    'Masala flavored snack',
    3
),

(
    'Coca Cola',
    'coca cola',
    'Carbonated soft drink',
    4
),

(
    'Pepsi',
    'pepsi',
    'Carbonated soft drink',
    4
),

(
    'Real Mixed Fruit Juice',
    'real mixed fruit juice',
    'Mixed fruit juice',
    4
),

(
    'Red Apple',
    'red apple',
    'Fresh red apple',
    5
),

(
    'Banana',
    'banana',
    'Fresh bananas',
    5
),

(
    'Tomato',
    'tomato',
    'Fresh tomatoes',
    6
),

(
    'Potato',
    'potato',
    'Fresh potatoes',
    6
),

(
    'Dove Soap',
    'dove soap',
    'Moisturizing bathing soap',
    7
),

(
    'Colgate Toothpaste',
    'colgate toothpaste',
    'Fluoride toothpaste',
    7
),

(
    'Surf Excel Detergent',
    'surf excel detergent',
    'Laundry detergent',
    8
);


-- ============================================================
-- INVENTORY
-- ============================================================

-- Sharma General Store

INSERT INTO inventory
(store_id, product_id, quantity, price, is_available)
VALUES
(1, 1, 25, 120, TRUE),
(1, 2, 18, 40, TRUE),
(1, 3, 20, 62, TRUE),
(1, 4, 10, 58, TRUE),
(1, 5, 15, 40, TRUE),
(1, 7, 30, 10, TRUE),
(1, 8, 12, 30, TRUE),
(1, 9, 20, 20, TRUE),
(1, 11, 10, 45, TRUE),
(1, 14, 15, 120, TRUE),
(1, 15, 25, 60, TRUE);


-- FreshMart

INSERT INTO inventory
(store_id, product_id, quantity, price, is_available)
VALUES
(2, 1, 8, 115, TRUE),
(2, 2, 25, 38, TRUE),
(2, 3, 30, 60, TRUE),
(2, 4, 15, 55, TRUE),
(2, 5, 20, 38, TRUE),
(2, 6, 10, 50, TRUE),
(2, 8, 20, 28, TRUE),
(2, 9, 35, 20, TRUE),
(2, 10, 18, 20, TRUE),
(2, 11, 20, 42, TRUE),
(2, 12, 15, 40, TRUE),
(2, 13, 12, 110, TRUE);


-- Gupta Grocery

INSERT INTO inventory
(store_id, product_id, quantity, price, is_available)
VALUES
(3, 1, 0, 125, FALSE),
(3, 3, 12, 62, TRUE),
(3, 5, 8, 42, TRUE),
(3, 7, 40, 10, TRUE),
(3, 8, 5, 32, TRUE),
(3, 9, 15, 22, TRUE),
(3, 10, 10, 20, TRUE),
(3, 15, 20, 55, TRUE),
(3, 16, 15, 40, TRUE),
(3, 17, 20, 35, TRUE);


-- City Supermarket

INSERT INTO inventory
(store_id, product_id, quantity, price, is_available)
VALUES
(4, 1, 40, 118, TRUE),
(4, 2, 30, 40, TRUE),
(4, 3, 50, 60, TRUE),
(4, 4, 25, 56, TRUE),
(4, 5, 30, 40, TRUE),
(4, 6, 20, 48, TRUE),
(4, 7, 50, 10, TRUE),
(4, 8, 25, 28, TRUE),
(4, 9, 40, 20, TRUE),
(4, 10, 30, 20, TRUE),
(4, 11, 30, 45, TRUE),
(4, 12, 25, 40, TRUE),
(4, 18, 15, 35, TRUE),
(4, 19, 10, 110, TRUE),
(4, 20, 10, 220, TRUE);


-- Local Needs Store

INSERT INTO inventory
(store_id, product_id, quantity, price, is_available)
VALUES
(5, 1, 5, 122, TRUE),
(5, 3, 10, 64, TRUE),
(5, 5, 5, 42, TRUE),
(5, 7, 15, 10, TRUE),
(5, 9, 10, 22, TRUE),
(5, 11, 8, 45, TRUE),
(5, 14, 10, 125, TRUE),
(5, 15, 15, 60, TRUE);


-- ============================================================
-- SALES
-- ============================================================

INSERT INTO sales
(store_id, total_amount, sold_at)
VALUES
(1, 1250, NOW() - INTERVAL '1 day'),
(1, 980, NOW() - INTERVAL '2 days'),
(1, 1540, NOW() - INTERVAL '3 days'),

(2, 2100, NOW() - INTERVAL '1 day'),
(2, 1750, NOW() - INTERVAL '2 days'),
(2, 2350, NOW() - INTERVAL '4 days'),

(3, 850, NOW() - INTERVAL '1 day'),
(3, 720, NOW() - INTERVAL '3 days'),

(4, 3200, NOW() - INTERVAL '1 day'),
(4, 2850, NOW() - INTERVAL '2 days'),
(4, 4100, NOW() - INTERVAL '4 days');


-- ============================================================
-- SALE ITEMS
-- ============================================================

INSERT INTO sale_items
(sale_id, product_id, quantity, unit_price, subtotal)
VALUES

(1, 1, 5, 120, 600),
(1, 7, 10, 10, 100),
(1, 9, 10, 20, 200),
(1, 3, 5, 62, 310),

(2, 1, 4, 120, 480),
(2, 3, 5, 62, 310),
(2, 5, 4, 40, 160),

(3, 1, 8, 120, 960),
(3, 8, 5, 30, 150),
(3, 11, 4, 45, 180),
(3, 5, 5, 40, 200),

(4, 1, 6, 115, 690),
(4, 3, 10, 60, 600),
(4, 9, 15, 20, 300),
(4, 13, 3, 110, 330),

(5, 1, 5, 115, 575),
(5, 7, 20, 10, 200),
(5, 11, 10, 42, 420),

(6, 1, 10, 115, 1150),
(6, 3, 10, 60, 600),
(6, 8, 10, 28, 280),

(7, 3, 5, 62, 310),
(7, 7, 20, 10, 200),
(7, 9, 10, 22, 220),

(8, 1, 4, 125, 500),
(8, 5, 5, 42, 210),

(9, 1, 12, 118, 1416),
(9, 3, 10, 60, 600),
(9, 7, 30, 10, 300),
(9, 9, 20, 20, 400),

(10, 1, 10, 118, 1180),
(10, 11, 10, 45, 450),
(10, 12, 10, 40, 400),

(11, 1, 15, 118, 1770),
(11, 3, 15, 60, 900),
(11, 8, 10, 28, 280),
(11, 10, 20, 20, 400);


-- ============================================================
-- SEARCH HISTORY
-- ============================================================

INSERT INTO search_history
(user_id, query, latitude, longitude)
VALUES
(1, 'chocolate', 30.3256, 78.0322),
(1, 'milk', 30.3256, 78.0322),
(1, 'sweet things', 30.3256, 78.0322),
(2, 'bread', 30.3475, 78.0550),
(3, 'snacks', 30.3310, 78.0045),
(4, 'cold drinks', 30.3165, 78.0322);


-- ============================================================
-- INVENTORY UPLOADS
-- ============================================================

INSERT INTO inventory_uploads
(
    store_id,
    file_name,
    file_type,
    status,
    total_records,
    successful_records,
    failed_records,
    uploaded_at,
    completed_at
)
VALUES
(
    1,
    'sharma_inventory.csv',
    'csv',
    'completed',
    120,
    116,
    4,
    NOW() - INTERVAL '10 days',
    NOW() - INTERVAL '10 days' + INTERVAL '2 minutes'
),
(
    2,
    'freshmart_inventory.csv',
    'csv',
    'completed',
    180,
    178,
    2,
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '7 days' + INTERVAL '3 minutes'
);


-- ============================================================
-- DEMO PREDICTIONS
-- ============================================================

INSERT INTO predictions
(
    store_id,
    product_id,
    predicted_quantity,
    confidence,
    prediction_date
)
VALUES
(1, 1, 32, 86.00, CURRENT_DATE + 7),
(1, 3, 25, 79.00, CURRENT_DATE + 7),
(1, 7, 45, 91.00, CURRENT_DATE + 7),

(2, 1, 28, 88.00, CURRENT_DATE + 7),
(2, 3, 40, 84.00, CURRENT_DATE + 7),

(4, 1, 55, 93.00, CURRENT_DATE + 7),
(4, 7, 70, 89.00, CURRENT_DATE + 7);


COMMIT;


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT 'users' AS table_name, COUNT(*) AS records FROM users
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'stores', COUNT(*) FROM stores
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL
SELECT 'sales', COUNT(*) FROM sales
UNION ALL
SELECT 'sale_items', COUNT(*) FROM sale_items
UNION ALL
SELECT 'search_history', COUNT(*) FROM search_history
UNION ALL
SELECT 'inventory_uploads', COUNT(*) FROM inventory_uploads
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions;