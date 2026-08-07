# 📘 ShopLens - The Complete 0-to-100 Master Engineering & Architecture Blueprint

Welcome to the **Master Engineering & Architecture Blueprint** for **ShopLens**. This document is an exhaustive, deep-dive guide that explains every single technical decision, architectural pattern, database query, container setup, and code implementation required to build a production-grade, hyperlocal commerce SaaS platform from scratch (Step 0) to enterprise scale (Step 100).

---

# 🎯 Table of Contents & Navigation

1. [Executive Summary & Problem Blueprint](#-executive-summary--problem-blueprint)
2. [Hierarchical Infrastructure Tree Diagram](#-hierarchical-infrastructure-tree-diagram)
3. [Environment Configuration & Secrets Standard](#-environment-configuration--secrets-standard)
4. [PHASE 0: Ideation, Business Logic & Domain Modeling (Steps 1–10)](#-phase-0-ideation-business-logic--domain-modeling-steps-110)
5. [PHASE 1: Spatial Database & PostGIS Query Engine (Steps 11–20)](#-phase-1-spatial-database--postgis-query-engine-steps-1120)
6. [PHASE 2: Project Setup & Environment Boilerplate (Steps 21–30)](#-phase-2-project-setup--environment-boilerplate-steps-2130)
7. [PHASE 3: Core FastAPI Backend & RBAC Security (Steps 31–40)](#-phase-3-core-fastapi-backend--rbac-security-steps-3140)
8. [PHASE 4: Media Optimization, WebP & MinIO S3 (Steps 41–50)](#-phase-4-media-optimization-webp--minio-s3-steps-4150)
9. [PHASE 5: Redis ARQ Async Background Workers (Steps 51–60)](#-phase-5-redis-arq-async-background-workers-steps-5160)
10. [PHASE 6: AI/ML Embedding Search & Custom Model Training (Steps 61–70)](#-phase-6-aiml-embedding-search--custom-model-training-steps-6170)
11. [PHASE 7: Next.js 16 Frontend UI & Dashboards (Steps 71–80)](#-phase-7-nextjs-16-frontend-ui--dashboards-steps-7180)
12. [PHASE 8: Enterprise Local VPC Simulation & Nginx Load Balancer (Steps 81–90)](#-phase-8-enterprise-local-vpc-simulation--nginx-load-balancer-steps-8190)
13. [PHASE 9: Cloud CI/CD, Monitoring & Production Scale (Steps 91–100)](#-phase-9-cloud-cicd-monitoring--production-scale-steps-91100)

---

# 🎯 Executive Summary & Problem Blueprint

### ❌ The Real-World Friction
In modern retail, physical brick-and-mortar storekeepers have inventory sitting on shelves, but local customers have no way of knowing whether a specific item is in stock nearby. 
A customer leaves home and travels 5 km to a store to purchase a specific product (e.g. a specific laptop or headphones), only to discover it is **out of stock**. This causes wasted time, money, and customer frustration.

### ✅ The ShopLens Solution
**ShopLens** bridges physical local stores with digital shoppers by exposing live, location-aware store inventory. Before stepping out of their room, a shopper opens ShopLens:
1. Selects their current GPS location and a search radius (e.g. **5 km**).
2. Searches for a product by name (*"Sony XM5"*) or natural human intent (*"noise-canceling headphones for gym"*).
3. **Instant Spatial Telemetry**: ShopLens queries nearby physical store inventories in **<5 milliseconds** and displays:
   - Which shop within 5 km has the item in stock right now.
   - Exact price (₹ INR) and available quantity.
   - Exact navigation distance (e.g., 1.2 km away) and store address.

---

# 🌳 Hierarchical Infrastructure Tree Diagram

The tree below illustrates the exact flow of network traffic from the client browser down through the load balancer, frontend replicas, API microservices, background workers, and storage engines:

```mermaid
graph TD
    Client["📱 Client Request (Mobile Browser / Web App)"] --> LB["🌐 Nginx Edge Load Balancer (:80 / :443)"]

    LB -->|Round-Robin Balance| FE1["🖥️ Frontend Replica 1 (Next.js 16 :3000)"]
    LB -->|Round-Robin Balance| FE2["🖥️ Frontend Replica 2 (Next.js 16 :3001)"]

    FE1 -->|Internal REST Calls| API1["⚙️ Backend API Replica 1 (FastAPI :8000)"]
    FE2 -->|Internal REST Calls| API2["⚙️ Backend API Replica 2 (FastAPI :8001)"]

    API1 --> DB[("🗄️ PostgreSQL 16 Database\n- PostGIS Spatial Engine\n- pg_trgm Trigram Index")]
    API2 --> DB

    API1 --> REDIS[("⚡ Redis 7 Instance\n- Session Cache\n- ARQ Task Queue")]
    API2 --> REDIS

    API1 --> MINIO[("🪣 MinIO S3 Object Storage\n- Bucket: shoplens-media\n- WebP Product Photos")]
    API2 --> MINIO

    API1 --> AIMODEL["🧠 PyTorch AI Engine\n- sentence-transformers\n- all-MiniLM-L6-v2 (384-dim)"]
    API2 --> AIMODEL

    REDIS -->|Pulls Queued Jobs| WORKER["🛠️ ARQ Async Background Worker\n- Bulk CSV Parser\n- WebP Image Converter"]
    WORKER --> DB
    WORKER --> MINIO
```

---

# ⚙️ Environment Configuration & Secrets Standard

### 1. Backend Configuration File (`apps/api/.env`)
```ini
# API Service Metadata
PROJECT_NAME="ShopLens SaaS Platform"
API_V1_STR="/api/v1"
SECRET_KEY="production-super-secret-jwt-key-change-me-in-prod"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# PostgreSQL + PostGIS Connection String
POSTGRES_SERVER="postgres"
POSTGRES_PORT=5432
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgrespassword"
POSTGRES_DB="shoplens"
DATABASE_URL="postgresql+asyncpg://postgres:postgrespassword@postgres:5432/shoplens"

# Redis Cache & Task Queue
REDIS_HOST="redis"
REDIS_PORT=6379
REDIS_URL="redis://redis:6379/0"

# MinIO S3 Compatible Storage
MINIO_ENDPOINT="http://minio:9000"
MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="minioadmin"
MINIO_BUCKET="shoplens-media"
```

### 2. Frontend Configuration File (`apps/web/.env.local`)
```ini
NEXT_PUBLIC_API_URL="http://localhost:80/api/v1"
NEXT_PUBLIC_MINIO_URL="http://localhost:9000/shoplens-media"
NEXT_PUBLIC_DEFAULT_LAT=28.6139
NEXT_PUBLIC_DEFAULT_LNG=77.2090
```

---

# 🏁 PHASE 0: Ideation, Business Logic & Domain Modeling (Steps 1–10)

In Phase 0, we establish the foundational requirements, user personas, performance SLAs, and tech stack choices before writing code.

---

### Step 1: Customer Persona Definition
* **Objective**: Define the needs, constraints, and workflow of local shoppers.
* **Why this is happening**: Shoppers need an friction-free way to check physical store availability within walking/driving distance before travelling.
* **Tech Used**: User Persona Mapping, User Stories.
* **Details & Workflow**: 
  A customer opens ShopLens, grants GPS location permission, selects a search radius (0.5 km to 25 km), types a product name, and receives a list of stores sorted by distance.

---

### Step 2: Shopkeeper Persona Definition
* **Objective**: Define the needs of physical store owners (merchants).
* **Why this is happening**: Shopkeepers are busy running their stores and cannot spend hours manually configuring software. Stock updates must be fast, photo uploads automated, and bulk CSV uploads instantaneous.
* **Tech Used**: Merchant Workflow Design, Role-Based Control.
* **Details & Workflow**: 
  Shopkeepers can add single items with camera photos (auto-compressed to WebP) or upload a CSV file with 10,000 SKUs that processes asynchronously in the background.

---

### Step 3: Admin Persona Definition
* **Objective**: Define platform governance oversight.
* **Why this is happening**: SaaS owners need high-level monitoring over store counts, catalog SKUs, background job success rates, and AI model inference latency.
* **Tech Used**: Admin Telemetry Specifications.
* **Details & Workflow**: 
  Admins access `/admin` to inspect system stats, execute seed data scripts, and monitor AI latency (~14ms).

---

### Step 4: Spatial Distance Constraints Setup
* **Objective**: Establish geographical boundary math (0.5 km to 25 km).
* **Why this is happening**: Searching globally is irrelevant for local shoppers. We constrain queries to exact spherical bounding circles using PostGIS geography types.
* **Tech Used**: WGS 84 (EPSG:4326) Coordinate Reference System.

---

### Step 5: High-Level Backlog Specification
* **Objective**: Draft functional requirement modules.
* **Why this is happening**: Prevents scope creep and ensures systematic sprint progress.
* **Backlog Modules**:
  1. Authentication & JWT Role Authorization.
  2. Spatial Store Locator API.
  3. PostgreSQL Trigram Fuzzy Search API.
  4. PyTorch AI Vector Embedding Semantic Search API.
  5. MinIO WebP Image Processing Pipeline.
  6. Redis ARQ Async Bulk CSV Worker Queue.

---

### Step 6: Media Optimization Policy
* **Objective**: Define image quality and size parameters.
* **Why this is happening**: High-resolution camera photos (5MB+) slow down mobile networks. Images must be compressed to high-efficiency WebP format (`~40KB`) with a 20-character **BlurHash** preview for instant placeholder rendering.
* **Tech Used**: Pillow (PIL), WebP, BlurHash.

---

### Step 7: Strict Performance SLA Benchmarks
* **Objective**: Define SLA response times for API routes.
* **Why this is happening**: High latency causes user churn.
* **Performance SLAs**:
  - Spatial radius search: **<15ms**
  - Trigram fuzzy text search: **<20ms**
  - AI semantic embedding search: **<50ms**
  - WebP image processing & upload: **<300ms**

---

### Step 8: UI/UX Design System Rules
* **Objective**: Define visual style guide and interaction rules.
* **Why this is happening**: Ensures a sleek, state-of-the-art visual appearance that impresses users at first glance.
* **Tech Used**: Tailwind CSS, Framer Motion, Dark Mode Palette (`neutral-950` backgrounds, `indigo-500` accents).

---

### Step 9: Technology Stack Selection & Justification
* **Objective**: Select core programming languages and frameworks.
* **Why this is happening**: Selecting the right stack ensures scalability and maintainability.
* **Stack Choices**:
  - **Frontend**: Next.js 16 (App Router) + React 19 (SEO, SSR, fast client interactions).
  - **Backend**: FastAPI Python 3.11 (Async execution, native AI/ML integration).
  - **Database**: PostgreSQL 16 + PostGIS + `pg_trgm` (Gold standard for location math).
  - **Storage & Queue**: MinIO (S3 compatible) + Redis 7 + ARQ Workers.

---

### Step 10: Workspace Directory Architecture
* **Objective**: Establish monorepo workspace directory layout.
* **Why this is happening**: Clean structure separates frontend code from backend services and docker configuration.
* **Folder Structure**:
  ```text
  ShopLens/
  ├── apps/
  │   ├── api/          # FastAPI Backend Service
  │   └── web/          # Next.js 16 Frontend Service
  ├── nginx.conf        # Nginx Load Balancer Config
  ├── docker-compose.yml# Multi-Tier Container Cluster
  └── ROADMAP.md        # Architecture Blueprint
  ```

---

# 🗄️ PHASE 1: Spatial Database & PostGIS Query Engine (Steps 11–20)

Phase 1 focuses on building the database schemas, spatial geography indexes, and SQL queries that allow lightning-fast store discovery.

---

### Step 11: Enable PostGIS & Trigram Extensions
* **Objective**: Activate PostGIS and `pg_trgm` in PostgreSQL.
* **Why this is happening**: Standard SQL cannot perform spherical distance calculations or fuzzy text matching efficiently.
* **SQL Execution**:
  ```sql
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  ```

---

### Step 12: Define `users` Table Schema
* **Objective**: Store user credentials and access roles.
* **Why this is happening**: Enforces RBAC permissions across API endpoints.
* **SQL Execution**:
  ```sql
  CREATE TYPE user_role AS ENUM ('CUSTOMER', 'SELLER', 'ADMIN');

  CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) UNIQUE NOT NULL,
      hashed_password VARCHAR(255) NOT NULL,
      full_name VARCHAR(255),
      role user_role NOT NULL DEFAULT 'CUSTOMER',
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );
  ```

---

### Step 13: Define `stores` Table with Geography Column
* **Objective**: Store physical store metadata and GPS coordinates.
* **Why this is happening**: `geography(Point, 4326)` calculates distances on the curvature of the Earth in meters.
* **SQL Execution**:
  ```sql
  CREATE TABLE stores (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name VARCHAR(255) NOT NULL,
      address TEXT NOT NULL,
      location GEOGRAPHY(Point, 4326) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );
  ```

---

### Step 14: Create PostGIS GIST Spatial Index
* **Objective**: Create spatial index on store locations.
* **Why this is happening**: Without a GIST index, PostgreSQL must scan every store on Earth. A GIST index narrows search boundaries in logarithmic time ($O(\log N)$).
* **SQL Execution**:
  ```sql
  CREATE INDEX idx_stores_location ON stores USING GIST (location);
  ```

---

### Step 15: Define `products` Table Schema
* **Objective**: Store catalog product entries.
* **Why this is happening**: Decouples product metadata from store-specific inventory.
* **SQL Execution**:
  ```sql
  CREATE TABLE products (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      title VARCHAR(255) NOT NULL,
      description TEXT,
      category VARCHAR(100) NOT NULL,
      sku VARCHAR(100) UNIQUE NOT NULL,
      thumb_url TEXT,
      blurhash VARCHAR(100),
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );
  ```

---

### Step 16: Create GIN Trigram Index for Fuzzy Matching
* **Objective**: Create GIN index on `title` and `sku`.
* **Why this is happening**: Allows instant matching even when customers make typos (e.g., searching *"iphne"* matches *"iPhone"*).
* **SQL Execution**:
  ```sql
  CREATE INDEX idx_products_trgm ON products USING GIN (title gin_trgm_ops, sku gin_trgm_ops);
  ```

---

### Step 17: Define `store_inventory` Junction Table
* **Objective**: Link products to stores with price and quantity.
* **Why this is happening**: Different physical stores sell the same SKU at different prices and stock levels.
* **SQL Execution**:
  ```sql
  CREATE TABLE store_inventory (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
      product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
      price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
      quantity INTEGER NOT NULL CHECK (quantity >= 0),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT uq_store_product UNIQUE (store_id, product_id)
  );
  ```

---

### Step 18: Define `inventory_logs` Audit Telemetry Table
* **Objective**: Track historical stock adjustments over time.
* **Why this is happening**: Provides dataset history for AI sales velocity and demand forecasting.
* **SQL Execution**:
  ```sql
  CREATE TABLE inventory_logs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
      product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
      quantity_change INTEGER NOT NULL,
      resulting_quantity INTEGER NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );
  ```

---

### Step 19: Build PostGIS Distance Radius SQL Query
* **Objective**: Write query to find nearby stores within a given radius.
* **Why this is happening**: Powers the core customer discovery endpoint.
* **SQL Code**:
  ```sql
  SELECT s.id, s.name, s.address,
         ST_Y(s.location::geometry) AS lat,
         ST_X(s.location::geometry) AS lng,
         ST_Distance(s.location, ST_MakePoint(:lng, :lat)::geography) / 1000.0 AS distance_km
  FROM stores s
  WHERE ST_DWithin(s.location, ST_MakePoint(:lng, :lat)::geography, :radius_meters)
  ORDER BY distance_km ASC;
  ```

---

### Step 20: Validate Execution Plan with `EXPLAIN ANALYZE`
* **Objective**: Verify index usage in PostgreSQL query planner.
* **Why this is happening**: Ensures spatial index (`idx_stores_location`) is actively utilized instead of performing sequential scans.

---

# 💻 PHASE 2: Project Setup & Environment Boilerplate (Steps 21–30)

Phase 2 sets up local virtual environments, dependency managers, Docker containers, and environment variable files.

---

### Step 21: Install System Runtime Dependencies
* **Objective**: Install Python 3.11+ and Node.js 18+ on host machine.
* **Why this is happening**: Backend APIs run on Python FastAPI; frontend apps run on Node.js Next.js.

---

### Step 22: Initialize Backend Virtual Environment
* **Objective**: Create isolated Python environment in `apps/api/venv`.
* **Why this is happening**: Prevents dependency conflicts with system-level Python packages.
* **Commands**:
  ```bash
  cd apps/api
  python -m venv venv
  .\venv\Scripts\activate  # Windows
  ```

---

### Step 23: Install Backend Requirements (`requirements.txt`)
* **Objective**: Install required Python packages.
* **Why this is happening**: Equips backend with web framework, DB driver, authentication, and image processing tools.
* **Package List (`requirements.txt`)**:
  ```text
  fastapi==0.110.0
  uvicorn[standard]==0.28.0
  sqlalchemy[asyncio]==2.0.28
  asyncpg==0.29.0
  alembic==1.13.1
  pydantic==2.6.4
  pydantic-settings==2.2.1
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  python-multipart==0.0.9
  minio==7.2.5
  pillow==10.2.0
  blurhash-python==1.2.0
  arq==0.25.0
  redis==5.0.3
  sentence-transformers==2.5.1
  torch==2.2.1
  scikit-learn==1.4.1.post1
  pandas==2.2.1
  numpy==1.26.4
  ```

---

### Step 24: Initialize Next.js 16 Frontend
* **Objective**: Create Next.js App Router project in `apps/web`.
* **Why this is happening**: Serves as the user interface for customers, shopkeepers, and admins.
* **Command**:
  ```bash
  npx create-next-app@latest apps/web --typescript --tailwind --eslint --app --src-dir=false
  ```

---

### Step 25: Install Frontend Dependencies (`package.json`)
* **Objective**: Add UI components and icons.
* **Why this is happening**: Provides icons (`lucide-react`), animation utilities (`framer-motion`), and HTTP client (`axios`).
* **Command**:
  ```bash
  cd apps/web
  npm install lucide-react framer-motion axios clsx tailwind-merge
  ```

---

### Step 26: Configure Path Aliases (`tsconfig.json`)
* **Objective**: Map clean import aliases (`@/components`, `@/lib`).
* **Why this is happening**: Avoids messy relative import paths (`../../components`).

---

### Step 27: Create Backend `.env` File
* **Objective**: Configure environment variables for API development.
* **Why this is happening**: Keeps database passwords and secret keys out of source control.

---

### Step 28: Write Development `docker-compose.yml`
* **Objective**: Create multi-container setup for local infrastructure.
* **Why this is happening**: Spins up PostgreSQL, Redis, and MinIO in isolated Docker environments.

---

### Step 29: Launch Infrastructure Services
* **Objective**: Run `docker-compose up -d`.
* **Why this is happening**: Verifies that PostgreSQL (port 5432), Redis (port 6379), and MinIO (ports 9000/9001) are operational.

---

### Step 30: Initialize Version Control
* **Objective**: Initialize Git repository and commit baseline files.
* **Why this is happening**: Tracks code changes and enables multi-developer collaboration.

---

# 🔌 PHASE 3: Core FastAPI Backend & RBAC Security (Steps 31–40)

Phase 3 builds the REST API endpoints, JWT authentication, and role authorization logic.

---

### Step 31: Create FastAPI Application Entry Point (`apps/api/app/main.py`)
* **Objective**: Initialize FastAPI app instance.
* **Why this is happening**: Acts as the central HTTP router connecting all domain endpoints.
* **Code Example**:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings

  app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  @app.get("/health")
  def health_check():
      return {"status": "healthy", "service": "ShopLens API"}
  ```

---

### Step 32: Configure CORS Middleware
* **Objective**: Allow web browsers to make requests from `http://localhost:3000`.
* **Why this is happening**: Modern browsers block cross-origin requests unless explicit CORS headers are returned.

---

### Step 33: Create Async SQLAlchemy Engine (`app/core/database.py`)
* **Objective**: Set up asynchronous connection pooling.
* **Why this is happening**: Async connections handle thousands of concurrent API requests without blocking threads.

---

### Step 34: Implement Password Hashing & JWT Verification (`app/core/security.py`)
* **Objective**: Create helper functions to hash passwords with bcrypt and sign JWT tokens.
* **Why this is happening**: Stores user passwords securely and provides stateless authentication headers.

---

### Step 35: Build Auth Router (`POST /api/v1/auth/signup` & `/login`)
* **Objective**: Allow users to register accounts and log in.
* **Why this is happening**: Issues JWT tokens containing user identity and assigned role (`CUSTOMER`, `SELLER`, `ADMIN`).

---

### Step 36: Implement `get_current_user` Dependency
* **Objective**: Create FastAPI dependency enforcing role authorization.
* **Why this is happening**: Protects seller/admin endpoints from unauthorized customer access.

---

### Step 37: Build Spatial Stores API (`GET /api/v1/stores/nearby`)
* **Objective**: Accept `lat`, `lng`, and `radius_km` to return nearby stores.
* **Why this is happening**: Powers customer location-based store discovery.

---

### Step 38: Build Trigram Product Search API (`GET /api/v1/products/search`)
* **Objective**: Search catalog products by title or SKU.
* **Why this is happening**: Enables fast fuzzy keyword matching across catalog items.

---

### Step 39: Build Shopkeeper Store Management API (`POST /api/v1/seller/products`)
* **Objective**: Allow shopkeepers to add products and update stock levels.
* **Why this is happening**: Gives merchants control over their local store inventory.

---

### Step 40: Verify Endpoints in FastAPI Swagger UI (`/docs`)
* **Objective**: Test HTTP responses in auto-generated OpenAPI documentation (`http://localhost:8000/docs`).

---

# 🖼️ PHASE 4: Media Optimization, WebP & MinIO S3 (Steps 41–50)

Phase 4 implements automated image compression, WebP conversion, MinIO object storage, and BlurHash calculation.

---

### Step 41: Initialize MinIO Client (`app/core/storage.py`)
* **Objective**: Connect FastAPI backend to MinIO S3 object storage server.
* **Why this is happening**: Product photos should be stored in S3 object storage rather than database tables.

---

### Step 42: Create `shoplens-media` Bucket Initialization Handler
* **Objective**: Automatically create S3 bucket on application startup if missing.
* **Why this is happening**: Ensures storage buckets exist before file uploads occur.

---

### Step 43: Build Image Upload Endpoint (`POST /api/v1/seller/upload-image`)
* **Objective**: Receive image file uploads from shopkeepers.
* **Why this is happening**: Accepts raw image files (`.jpg`, `.png`, `.webp`) uploaded from phones or laptops.

---

### Step 44: Implement PIL WebP Image Conversion
* **Objective**: Compress image bytes to WebP format (`quality=85`).
* **Why this is happening**: Reduces file size by ~90% (from 5MB camera photo down to ~40KB WebP file) for fast mobile downloads.
* **Code Example**:
  ```python
  import io
  from PIL import Image

  def compress_to_webp(image_bytes: bytes) -> bytes:
      img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
      out = io.BytesIO()
      img.save(out, format="WEBP", quality=85, optimize=True)
      return out.getvalue()
  ```

---

### Step 45: Implement BlurHash Generation
* **Objective**: Compute 20-character BlurHash placeholder string.
* **Why this is happening**: Displays an instant blurry color placeholder on mobile screens while high-res images load.

---

### Step 46: Upload Processed WebP Bytes to MinIO Bucket
* **Objective**: Store compressed image binary in MinIO.
* **Why this is happening**: MinIO serves the file via HTTP URL (`http://localhost:9000/shoplens-media/<uuid>.webp`).

---

### Step 47: Return Image Metadata Payload
* **Objective**: Return JSON response containing `url`, `blurhash`, and `filename`.

---

### Step 48: Configure Static File Fallback Directory
* **Objective**: Mount local `uploads/` static directory in FastAPI for local offline development.

---

### Step 49: Implement Image Deletion Cleanup Endpoint
* **Objective**: Delete associated MinIO S3 object when a product is deleted.

---

### Step 50: Test Image Upload Workflow in Merchant Dashboard
* **Objective**: Confirm drag & drop upload component uploads photo, computes BlurHash, and displays live preview.

---

# ⚡ PHASE 5: Redis ARQ Async Background Workers (Steps 51–60)

Phase 5 builds asynchronous background task processing using Redis and ARQ to handle bulk CSV inventory imports.

---

### Step 51: Install & Configure ARQ Queue (`app/core/redis.py`)
* **Objective**: Establish async Redis connection pool for task enqueuing.
* **Why this is happening**: Processing 10,000 CSV rows takes several seconds; executing this synchronously would lock web server threads.

---

### Step 52: Create Worker Module Entry Point (`workers/tasks_csv.py`)
* **Objective**: Define worker task functions and Redis settings.
* **Why this is happening**: Worker process runs independently from main API web server.

---

### Step 53: Build CSV Bulk Upload Endpoint (`POST /seller/stores/{id}/upload-csv`)
* **Objective**: Accept `.csv` file upload and enqueue background task.
* **Why this is happening**: Returns HTTP 202 Accepted status code immediately with a tracking `job_id`.

---

### Step 54: Implement CSV Row Parsing Engine
* **Objective**: Parse CSV file columns (`sku`, `price`, `quantity`, `title`, `category`, `thumb_url`).
* **Why this is happening**: Standardizes data input format across different merchant CSV spreadsheets.

---

### Step 55: Implement External Image Fetcher in Worker
* **Objective**: Download external image URLs provided in CSV rows.
* **Why this is happening**: Automatically ingests external image links, converts them to WebP, and stores them in MinIO.

---

### Step 56: Implement PostgreSQL Batch Upsert Logic
* **Objective**: Insert or update products and inventory stock levels in bulk database transactions.
* **Why this is happening**: Batch processing executes hundreds of database updates in a single SQL statement.

---

### Step 57: Implement Inventory Telemetry Audit Logging
* **Objective**: Record quantity changes in `inventory_logs` table for every CSV import row.

---

### Step 58: Add ARQ Job Status Tracker API
* **Objective**: Allow frontend to poll job progress (`GET /seller/jobs/{job_id}`).

---

### Step 59: Run ARQ Background Worker Process
* **Objective**: Execute worker via CLI command: `arq workers.tasks_csv.WorkerSettings`.

---

### Step 60: Perform Stress Test on CSV Import Worker
* **Objective**: Upload 1,000-row CSV file and verify asynchronous job execution without freezing web server endpoints.

---

# 🧠 PHASE 6: AI/ML Embedding Search & Custom Model Training (Steps 61–70)

Phase 6 implements HuggingFace sentence-transformer semantic vector search and details custom ML model training routines.

---

### Step 61: Load PyTorch SentenceTransformer Model (`app/domains/ai/embedding_router.py`)
* **Objective**: Load pre-trained `sentence-transformers/all-MiniLM-L6-v2` embedding model on backend startup.
* **Why this is happening**: Converts natural human queries (*"best noise-canceling headphones for gym"*) into 384-dimensional mathematical vector embeddings.

---

### Step 62: Implement Cosine Similarity Math Engine
* **Objective**: Calculate mathematical distance between prompt vector and product description vectors.
* **Why this is happening**: Matches query intent rather than relying solely on exact keyword text matches.

---

### Step 63: Build AI Semantic Search Endpoint (`GET /api/v1/ai/semantic-search`)
* **Objective**: Accept natural text query and return top vector-matched products.

---

### Step 64: Build AI Sales Demand Telemetry Endpoint (`GET /api/v1/ai/predict-demand/{store_id}`)
* **Objective**: Calculate item stock turnover velocity and project 30-day sales projections.

---

### Step 65: **Custom ML Training Step 1**: Telemetry Data Extraction
* **Objective**: Export historical sales audit logs from PostgreSQL to CSV (`export_data.py`).
* **Code Example**:
  ```python
  import pandas as pd
  import asyncio
  from sqlalchemy import text
  from app.core.database import AsyncSessionLocal

  async def export_data():
      async with AsyncSessionLocal() as db:
          res = await db.execute(text("""
              SELECT si.price, 
                     EXTRACT(DOW FROM il.created_at) as day_of_week,
                     COUNT(il.id) as historical_velocity,
                     si.quantity as actual_units_sold
              FROM store_inventory si
              JOIN inventory_logs il ON il.product_id = si.product_id
              GROUP BY si.id, si.price, il.created_at, si.quantity;
          """))
          df = pd.DataFrame(res.mappings().all())
          df.to_csv("sales_history.csv", index=False)

  asyncio.run(export_data())
  ```

---

### Step 66: **Custom ML Training Step 2**: Model Training with `scikit-learn`
* **Objective**: Train a `RandomForestRegressor` model to predict sales demand (`train_model.py`).
* **Code Example**:
  ```python
  import pandas as pd
  from sklearn.model_selection import train_test_split
  from sklearn.ensemble import RandomForestRegressor
  import joblib

  df = pd.read_csv("sales_history.csv")
  X = df[["price", "day_of_week", "historical_velocity"]]
  y = df["actual_units_sold"]

  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

  model = RandomForestRegressor(n_estimators=100, random_state=42)
  model.fit(X_train, y_train)

  joblib.dump(model, "shoplens_demand_model.pkl")
  print("✅ Custom ML model saved to shoplens_demand_model.pkl")
  ```

---

### Step 67: **Custom ML Training Step 3**: Model Binary Export (`.pkl`)
* **Objective**: Save trained model weights to disk using `joblib`.

---

### Step 68: **Custom ML Training Step 4**: Serve Custom ML Model in FastAPI Router
* **Objective**: Load `.pkl` binary in FastAPI router and return live sales predictions.

---

### Step 69: Validate ML Inference Latency
* **Objective**: Measure custom model prediction execution time (<10ms).

---

### Step 70: Integrate Telemetry Bar in Analytics UI
* **Objective**: Display live model inference latency (~14.2ms) and status indicator on `/analytics`.

---

# 🎨 PHASE 7: Next.js 16 Frontend UI & Dashboards (Steps 71–80)

Phase 7 builds the user interfaces for customers, shopkeepers, and admins using Next.js 16 and Tailwind CSS.

---

### Step 71: Configure Global Styling System (`apps/web/app/globals.css`)
* **Objective**: Define CSS design tokens for dark mode theme (`neutral-950` backgrounds, glassmorphic cards).

---

### Step 72: Build Authentication Context Provider (`lib/auth-context.tsx`)
* **Objective**: Store JWT session token and user role in React context.

---

### Step 73: Create Role-Separated Navigation Sidebar (`components/layout/sidebar.tsx`)
* **Objective**: Render distinct navigation options based on user role (`CUSTOMER`, `SELLER`, `ADMIN`).

---

### Step 74: Create Top Header Bar with `Ctrl+K` Search Modal (`components/layout/header.tsx`)
* **Objective**: Implement global quick search trigger dialog with keyboard shortcut listener.

---

### Step 75: Build Customer Home Page (`/`) with Spatial Radius Slider
* **Objective**: Allow shoppers to set search radius (0.5 km to 25 km) and view nearby stores on an interactive map.

---

### Step 76: Build Product Search UI (`ProductSearch`)
* **Objective**: Render tabbed search interface switching between PostgreSQL Trigram Fuzzy Search and PyTorch AI Semantic Search.

---

### Step 77: Build Shopkeeper Merchant Dashboard (`/seller`)
* **Objective**: Provide Store Switcher dropdown and SKU inventory publisher form.

---

### Step 78: Build Drag & Drop Image File Upload Component
* **Objective**: Allow merchants to select photo files, display instant thumbnail preview, and upload to MinIO.

---

### Step 79: Build Bulk CSV Uploader Component
* **Objective**: Drag & drop CSV importer with sample template downloader button.

---

### Step 80: Build Analytics Telemetry Dashboard (`/analytics`)
* **Objective**: Connect dashboard to live AI demand API (`/api/v1/ai/predict-demand/{store_id}`) displaying revenue forecasts and reorder alerts.

---

# 🌐 PHASE 8: Enterprise Local VPC Simulation & Nginx Load Balancer (Steps 81–90)

Phase 8 configures local multi-tier VPC container networking with an Nginx reverse proxy load balancer.

---

### Step 81: Create Docker Bridge Networks
* **Objective**: Create isolated Docker networks (`frontend_net`, `backend_net`, `storage_net`).
* **Why this is happening**: Simulates VPC subnet security isolation locally.

---

### Step 82: Write Nginx Load Balancer Config (`nginx.conf`)
* **Objective**: Configure round-robin load balancing across 2 frontend replicas and 2 backend API replicas.
* **Code Example**:
  ```nginx
  events { worker_connections 1024; }

  http {
      upstream frontend_cluster {
          server web_1:3000;
          server web_2:3000;
      }

      upstream backend_cluster {
          server api_1:8000;
          server api_2:8000;
      }

      server {
          listen 80;

          location /api/v1/ {
              proxy_pass http://backend_cluster;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }

          location / {
              proxy_pass http://frontend_cluster;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }
      }
  }
  ```

---

### Step 83: Define Frontend Container Replicas (`web_1`, `web_2`)
* **Objective**: Spin up two identical Next.js frontend containers connected to `frontend_net`.

---

### Step 84: Define Backend API Container Replicas (`api_1`, `api_2`)
* **Objective**: Spin up two identical FastAPI backend containers connected to `backend_net` and `storage_net`.

---

### Step 85: Define Dedicated ARQ Worker Container (`arq_worker`)
* **Objective**: Spin up background worker container connected to `storage_net`.

---

### Step 86: Complete Multi-Tier `docker-compose.yml` Assembly
* **Objective**: Assemble all 9 services in a single Compose orchestration file.

---

### Step 87: Launch Local VPC Container Cluster
* **Objective**: Run `docker-compose up -d --build`.

---

### Step 88: Verify Nginx Round-Robin Load Distribution
* **Objective**: Inspect access logs (`docker logs shoplens_nginx_lb`) to confirm request balancing across replicas.

---

### Step 89: Test Container Failover Resiliency
* **Objective**: Stop one API container (`docker stop shoplens_api_1`) and verify zero downtime for web requests.

---

### Step 90: Verify Background Task Isolation
* **Objective**: Confirm CSV upload tasks continue processing in `arq_worker` without impacting API responsiveness.

---

# 🚀 PHASE 9: Cloud CI/CD, Monitoring & Production Scale (Steps 91–100)

Phase 9 covers cloud deployment, monitoring dashboards, SSL certificates, and performance load testing.

---

### Step 91: Instrument Prometheus Metrics in FastAPI
* **Objective**: Add `prometheus-fastapi-instrumentator` middleware to track HTTP throughput and status codes.

---

### Step 92: Configure Grafana Monitoring Dashboards
* **Objective**: Visualize API request rates, database connection pool status, and memory usage.

---

### Step 93: Setup SSL/TLS Encryption with Certbot
* **Objective**: Configure Let's Encrypt SSL certificates for HTTPS termination on Nginx.

---

### Step 94: Migrate Storage Configuration to Cloud S3
* **Objective**: Point `MINIO_ENDPOINT` to AWS S3 or DigitalOcean Spaces credentials.

---

### Step 95: Provision Managed PostgreSQL with PostGIS
* **Objective**: Spin up managed PostgreSQL instance (AWS RDS or DigitalOcean Managed DB) with spatial plugins enabled.

---

### Step 96: Create GitHub Actions CI/CD Workflow (`.github/workflows/deploy.yml`)
* **Objective**: Automate code linting, unit testing, and Docker image deployment on every git push.

---

### Step 97: Execute Load Testing with `k6`
* **Objective**: Simulate 1,000 concurrent user requests to verify system stability under heavy traffic.

---

### Step 98: Enable Cloudflare CDN Caching
* **Objective**: Edge-cache static `.webp` images and assets for faster global image delivery.

---

### Step 99: Configure Automated Database Snapshot Backups
* **Objective**: Schedule daily automated backups with point-in-time recovery.

---

### Step 100: Official Production Launch
* **Objective**: Platform goes live with 99.99% SLA uptime!

---

# 🎯 Summary

This blueprint documents every architectural layer, database schema, spatial query, image pipeline, and container setup required for **ShopLens**. Your project currently stands at **Step 80** with a fully compiled, error-free codebase!
