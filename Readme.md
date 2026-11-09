# ShopLens — Hyperlocal Quick-Commerce Discovery & Search Platform

ShopLens is an intelligent, production-grade hyperlocal retail platform engineered to power instant grocery discovery (similar to Blinkit and Zepto). It features a multi-stage hybrid search engine combining **PostgreSQL Full-Text Search (`tsvector`)**, **typo-tolerant fuzzy search (`pg_trgm`)**, and **dense vector retrieval via `BAAI/bge-small-en-v1.5` with `pgvector`**, orchestrated with **Q2C leaf-node taxonomy routing**, **Reciprocal Rank Fusion (RRF)**, and **PostGIS geospatial filtering** across real-time multi-store inventory.

---

## Architecture & Search Pipeline Flow

```mermaid
flowchart TD
    UserReq["User Search Query + Geolocation<br/>(e.g., 'something to drink under 100')"] --> Normalizer

    subgraph STAGE_1 ["Stage 1: Normalization & Constraint Extraction"]
        Normalizer["Query Normalizer<br/>• Maps Hinglish ('doodh' -> 'milk', 'paani' -> 'water')<br/>• Extracts price constraints ('under 100' -> max_price=100)<br/>• Extracts radius ('within 5km' -> radius_km=5)<br/>• Strips filler tokens ('show me', 'near me')"]
        Normalizer --> FilterResolver["Filter Resolver<br/>Reconciles UI filters vs parsed natural language constraints"]
    end

    subgraph STAGE_2 ["Stage 2: Intent Classification & Taxonomy Routing"]
        FilterResolver --> Classifier["Intent Classifier & Taxonomy Matcher<br/>Evaluates against 13 Categories & 50 Subcategories"]
        Classifier -->|Type A: Specific Brand / Subcategory| GatedScope["Hard Taxonomy Gating<br/>Locks category & subcategory (Zero Leakage)"]
        Classifier -->|Type B: Broad / Conceptual Query| BroadScope["Conceptual Intent Routing<br/>Enforces Cosine Distance Floor on Allowed Categories"]
    end

    subgraph STAGE_3 ["Stage 3: Multi-Channel Retrieval"]
        GatedScope --> FTS["Full-Text Search (tsvector)<br/>Weighted title, brand, tags, specs"]
        GatedScope --> Fuzzy["Fuzzy Search (pg_trgm)<br/>Trigram typo tolerance"]
        GatedScope --> Vector["Dense Vector Search (pgvector)<br/>384-d BGE normalized embeddings"]
        
        BroadScope --> FTS
        BroadScope --> Fuzzy
        BroadScope --> Vector
    end

    subgraph STAGE_4 ["Stage 4: Hybrid Fusion & Business Ranking"]
        FTS --> RRF["Reciprocal Rank Fusion (RRF k=60)<br/>Fuses rank positions across all channels"]
        Fuzzy --> RRF
        Vector --> RRF
        RRF --> BusinessRanker["PostGIS & Inventory Ranker<br/>• Distance decay via ST_Distance (SRID 4326)<br/>• Stock availability & price constraints<br/>• Nearest store prioritization"]
    end

    BusinessRanker --> Response["Structured JSON Response<br/>[Products, Brands, Net Quantity, Store, Distance, Price]"]
```

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | Python 3.11+ / 3.14, FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings |
| **Database & ORM** | PostgreSQL 16, SQLAlchemy 2.0 (asyncio), AsyncPG, GeoAlchemy2 |
| **Database Extensions** | **PostGIS** 3.6 (geospatial), **pgvector** 0.8.7 (dense vector retrieval), **pg_trgm** (fuzzy trigram) |
| **Search Engine** | Dual-Path Q2C Leaf-Node Router, Reciprocal Rank Fusion (RRF $k=60$), Weighted tsvector BM25 |
| **Embedding Model** | **`BAAI/bge-small-en-v1.5`** (384-dimensional normalized dense vectors) |
| **Database Migrations** | Alembic (asyncpg configuration with PostGIS/pgvector compatibility) |
| **Frontend UI** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Hugeicons |
| **DevOps / Containers** | Docker & Docker Compose (custom PostGIS + pgvector multi-extension build) |
| **Automated Testing** | Pytest, Pytest-Cov, AnyIO, HTTPX (47 automated tests, 100% pass rate) |

---

## Catalog & Taxonomy Structure

ShopLens includes a comprehensive quick-commerce catalog of **850 realistic products** distributed across **13 master categories**, **50 granular subcategories**, and **4,250 store-inventory mappings** across 5 local stores:

```text
13 Master Categories:
├── Dairy, Bread & Eggs (Milk, Butter, Cheese, Bread, Eggs, Paneer, Curd...)
├── Drinks & Juices (Soft drinks, Fruit juices, Cold-pressed, Syrups, Energy drinks...)
├── Snacks & Munchies (Chips, Crisps, Popcorn, Namkeen, Puffs...)
├── Bakery & Biscuits (Cookies, Rusks, Cakes, Wafers...)
├── Sweets & Chocolates (Chocolates, Candies, Traditional sweets, Desserts...)
├── Instant & Frozen Foods (Noodles, Ready-to-eat meals, Frozen snacks...)
├── Fruits & Vegetables (Fresh seasonal produce, Exotic fruits...)
├── Cooking Essentials (Atta, Rice, Dals, Spices, Oils, Ghee, Sugar, Salt...)
├── Tea, Coffee & Health Drinks (Green tea, Instant coffee, Cocoa, Malt drinks...)
├── Breakfast & Sauces (Cereals, Oats, Spreads, Ketchups, Jams, Honey...)
├── Personal Care (Soaps, Shampoos, Oral care, Skincare...)
├── Cleaning & Household Essentials (Detergents, Surface cleaners, Utensil bars, Paper...)
└── Baby Care & Pet Supplies (Baby wipes, Dog food, Cat treats...)
```

---

## Repository Structure

```text
ShopLens/
├── backend/
│   ├── alembic/                      # Database migrations
│   │   ├── versions/
│   │   │   ├── 0001_baseline_schema.py    # Schema: tables, indexes, extensions
│   │   │   └── 0002_seed_initial_data.py  # Seed: 850 products & 4,250 inventory rows
│   │   └── env.py                    # Async migration engine configuration
│   ├── apis/v1/
│   │   ├── routes/
│   │   │   ├── auth.py               # User registration & JWT authentication
│   │   │   ├── inventory.py          # Store inventory management
│   │   │   ├── product.py            # Catalog endpoints
│   │   │   ├── search.py             # Production search: GET and POST endpoints
│   │   │   └── store.py              # Store profile & registration
│   │   └── schemas/
│   │       ├── auth.py
│   │       ├── inventory.py
│   │       ├── product.py
│   │       ├── search.py             # SearchRequest & SearchResponse schemas
│   │       └── store.py
│   ├── config.py                     # Centralized, type-safe settings (Pydantic)
│   ├── core/
│   │   ├── dependencies.py           # FastAPI auth dependencies
│   │   ├── logging.py                # Timestamped structured logger
│   │   ├── security.py               # Password hashing & JWT token issuance
│   │   └── taxonomy_data.py          # 13 Categories, 50 Subcategories & Synonyms
│   ├── db/
│   │   ├── database.py               # Async SQLAlchemy engine & session factory
│   │   └── models/                   # ORM models (Category, SubCategory, Product, Store, Inventory...)
│   ├── models/
│   │   └── embedding_model/          # Local BAAI/bge-small-en-v1.5 model files
│   ├── scripts/
│   │   └── generate_embeddings.py    # High-speed script to populate 384-d product embeddings
│   ├── services/
│   │   └── search/                   # Modular Search Subsystem
│   │       ├── search_service.py     # Master Pipeline Orchestrator
│   │       ├── query/                # Normalizer, Intent Classifier, Taxonomy Matcher, Filter Resolver
│   │       ├── retrieval/            # Vector Search, Full-Text Search, Fuzzy Search
│   │       └── ranking/              # Reciprocal Rank Fusion (RRF), Business Ranker, Reranker
│   ├── tests/                        # 47 automated tests (Unit, Integration & Benchmarks)
│   ├── requirements.txt              # Backend Python dependencies
│   └── main.py                       # FastAPI entrypoint application
├── database/
│   ├── 01-init.sql                   # Database initialization: extensions, schema & indexes
│   ├── 02-seed.sql                   # Full seed: 850 products, 5 stores, 4,250 inventory records
│   └── Dockerfile.pgvector           # Docker image building PostGIS 3.6 + pgvector 0.8.7
├── frontend/                         # Next.js 16 web application
├── docker-compose.yml                # Multi-container orchestration (PostgreSQL & pgAdmin)
└── README.md                         # Project documentation
```

---

## Step-by-Step Setup from Scratch

Follow these instructions to run the entire ShopLens platform locally after cloning the repository.

### Prerequisites

Ensure you have the following installed on your machine:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running with Linux containers)
- [Python](https://www.python.org/) 3.11 or newer (Python 3.12 / 3.14 supported)
- [Node.js](https://nodejs.org/) 18+ and `npm`

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/<your-username>/ShopLens.git
cd ShopLens
```

---

### Step 2: Configure Environment Variables

Create your backend `.env` file from the provided template:

**Windows (PowerShell):**
```powershell
Copy-Item backend\.env.example backend\.env
```

**macOS / Linux:**
```bash
cp backend/.env.example backend/.env
```

Verify that `backend/.env` contains your connection credentials:
```ini
DATABASE_URL=postgresql+asyncpg://shoplens:shoplens@localhost:5432/shoplens
JWT_SECRET_KEY=shoplens_super_secret_jwt_key_change_in_production_123456
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### Step 3: Start Database Services with Docker

Start PostgreSQL (equipped with PostGIS, pgvector, and pg_trgm) and pgAdmin:

```bash
docker compose up -d --build
```

- **PostgreSQL**: Port `5432` (Username: `shoplens`, Password: `shoplens`, Database: `shoplens`)
- **pgAdmin 4**: Port `5050` (Email: `admin@gmail.com`, Password: `admin`)

Verify the container is healthy:
```bash
docker ps
```

---

### Step 4: Setup Backend Virtual Environment

Navigate to the `backend` directory, create a virtual environment, and install dependencies:

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 5: Download the Embedding Model

ShopLens uses **`BAAI/bge-small-en-v1.5`** (384-dimensional dense vectors) for fast, local semantic retrieval.

- **Hugging Face Model Page**: [https://huggingface.co/BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5)

Download and place the model directly into `backend/models/embedding_model/`:

#### Option A: One-Liner via Python (Recommended)
From the `backend/` directory with your virtual environment active, run:
```bash
python -c "from sentence_transformers import SentenceTransformer; print('Downloading BGE model...'); SentenceTransformer('BAAI/bge-small-en-v1.5').save('models/embedding_model'); print('Model saved to backend/models/embedding_model successfully!')"
```

#### Option B: Clone via Git LFS
```bash
git clone https://huggingface.co/BAAI/bge-small-en-v1.5 backend/models/embedding_model
```

#### Option C: Manual Download from Browser
1. Visit [https://huggingface.co/BAAI/bge-small-en-v1.5/tree/main](https://huggingface.co/BAAI/bge-small-en-v1.5/tree/main).
2. Download the repository files.
3. Save them inside `backend/models/embedding_model/`.

---

### Step 6: Run Database Migrations (Schema & 850 Products Seed)

Alembic establishes the database schema baseline and seeds the catalog. From the `backend` directory:

```bash
# Set PYTHONPATH to the backend directory
# Windows (PowerShell): $env:PYTHONPATH="."
# Linux/macOS: export PYTHONPATH="."

# Run migrations up to head
alembic upgrade head
```

This applies two migrations:
1. `0001_baseline_schema`: Sets up tables, PostGIS/pgvector/pg_trgm extensions, and GIN/GiST indexes.
2. `0002_seed_initial_data`: Populates 13 categories, 50 sub-categories, 5 stores, 850 products, and 4,250 inventory rows.

Verify the current migration:
```bash
alembic current
```
*Expected: `0002_seed_initial_data (head)`*

---

### Step 7: Generate Vector Embeddings for Catalog

Compute and store normalized 384-dimensional dense embeddings in PostgreSQL for all 850 products:

```bash
# Run from the backend directory
python scripts/generate_embeddings.py
```
*Output: `Processed 850/850 products... Embedding generation completed successfully for all products.`*

---

### Step 8: Run Automated Tests

Run the full automated test suite (47 tests covering normalizer, filter resolver, intent classifier, RRF fusion, API endpoints, and live queries):

```bash
pytest tests -v
```

Expected result:
```text
============================= 47 passed in ~4.7s =============================
```

---

### Step 9: Start the FastAPI Backend Server

Launch the backend with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Step 10: Setup and Run Frontend (Next.js)

In a separate terminal, start the Next.js frontend:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at **[http://localhost:3000](http://localhost:3000)** to search and discover local products.

---

## Search Engine Features & Algorithms

### 1. Hinglish & Conversational Normalization (`services/search/query/normalizer.py`)
- Translates common conversational Hinglish tokens (e.g. `doodh` $\rightarrow$ `milk`, `paani` $\rightarrow$ `water`, `cheeni` $\rightarrow$ `sugar`, `chawal` $\rightarrow$ `rice`).
- Extracts price constraints (e.g., `"under 50"`, `"below Rs 200"`, `"100 se kam"`).
- Extracts radius constraints (e.g., `"within 3 km"`, `"under 5 miles"`).
- Strips conversational stop words (e.g., `"show me"`, `"give me"`, `"near me"`).

### 2. Intent Classification & Q2C Taxonomy Gating (`services/search/query/`)
- **Type A (Specific Query)**: When a query matches an entity (e.g., brand `"Amul"`, item `"Chocolate"`, subcategory `"Milk"`), the engine locks the candidate scope to the exact category/subcategory. **Zero unrelated category leakage** (e.g. chips will never appear for "chocolate").
- **Type B (Conceptual Query)**: For discovery phrases (e.g. `"something to drink"`, `"something sweet"`, `"household cleaning items"`), the engine routes to multiple semantic subcategories and applies a cosine distance floor to prevent unrelated false positives.

### 3. Multi-Channel Retrieval (`services/search/retrieval/`)
- **Vector Search (`pgvector`)**: 384-dimensional dense semantic vectors using `BAAI/bge-small-en-v1.5`.
- **Full-Text Search (`tsvector`)**: Weighted lexical matching across Title (weight A), Brand (weight A), Subcategory/Tags (weight B), and Description (weight C).
- **Fuzzy Search (`pg_trgm`)**: Trigram typo tolerance (threshold 0.25) to catch misspellings like `"choclate"`.

### 4. Reciprocal Rank Fusion (`services/search/ranking/rrf.py`)
Fuses candidate ranks from all active channels using standard RRF ($k=60$):
$$RRF\_Score(d) = \sum_{c \in Channels} \frac{1}{k + Rank_c(d)}$$
Products corroborated across multiple retrieval channels receive substantial ranking boosts.

### 5. PostGIS Proximity & Inventory Join (`services/search/ranking/business_ranker.py`)
- Filters stores within the user's geofenced radius using `ST_DWithin` on `stores.location` (SRID 4326).
- Computes real-time geodesic distances using `ST_Distance`.
- Applies distance penalty and availability boosts to prioritize in-stock items from the nearest neighborhood stores.

---

## API Documentation

### Product Search Endpoints

#### 1. POST Search (Recommended for Apps & Frontend)
`POST /api/v1/search/products`

**Request Body:**
```json
{
  "query": "something sweet under 200",
  "latitude": 30.3256,
  "longitude": 78.0322,
  "radius_km": 10.0,
  "min_price": null,
  "max_price": null,
  "limit": 10
}
```

**Response Body:**
```json
{
  "query": "something sweet under 200",
  "normalized_query": "something sweet",
  "applied_filters": {
    "min_price": null,
    "max_price": 200.0,
    "radius_km": 10.0,
    "category_id": null
  },
  "total_results": 10,
  "results": [
    {
      "product_id": 142,
      "product_name": "Cadbury Dairy Milk Silk Chocolate Bar",
      "brand": "Cadbury",
      "sub_category_name": "Chocolates & Candies",
      "net_quantity": "150 g",
      "category_name": "Sweets & Chocolates",
      "price": 175.0,
      "mrp": 190.0,
      "quantity": 25,
      "is_available": true,
      "store": {
        "id": 1,
        "name": "Sharma General Store",
        "address": "Rajpur Road, Dehradun"
      },
      "distance_km": 1.25,
      "score": 0.0482,
      "sources": ["vector", "fts"]
    }
  ]
}
```

#### 2. GET Search (Quick Browser & URL Queries)
`GET /api/v1/search?q=chocolate&latitude=30.3256&longitude=78.0322&radius_km=5.0`

---

## Git & Repository Best Practices

- **Do not commit `.env`**: Credentials and local database passwords must stay private. Use `.env.example` as the shared template.
- **Do not commit large model weights (`.safetensors`, `.bin`)**: Download the weights into `backend/models/embedding_model/` using the instructions in Step 5.
- **Do not commit cache files**: `__pycache__/`, `.pytest_cache/`, and `.next/` are properly excluded in `.gitignore`.
