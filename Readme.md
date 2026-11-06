# ShopLens — Hyperlocal Grocery Discovery & Search Platform

ShopLens is an intelligent, hyperlocal retail platform that bridges the gap between neighborhood brick-and-mortar grocery stores and consumers. It features a multi-channel hybrid search engine combining **exact keyword matching**, **typo-tolerant fuzzy search**, and a **fine-tuned domain-specific Sentence Transformer with pgvector semantic retrieval**, coupled with **PostGIS geospatial filtering** and real-time inventory management.

---

## Architecture Overview

```
                      User Search Request
       [Query String (e.g. "sweet snacks under 50") + Geo Coordinates]
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │         Query Normalizer             │
               │ • Extract price constraints (min/max)│
               │ • Extract radius intent (km/miles)   │
               │ • Clean conversational filler tokens │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │           Filter Resolver            │
               │ • Explicit UI filters take precedence│
               │ • Fallback to normalized query terms │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │   Multi-Channel Retrieval Engine     │
               │                                      │
               │ 1. Keyword Channel (SQL ILIKE)       │
               │    -> Exact & substring token match  │
               │                                      │
               │ 2. Fuzzy Channel (Postgres pg_trgm)  │
               │    -> Trigram similarity (typos)     │
               │                                      │
               │ 3. Semantic Channel (pgvector)       │
               │    -> 384-d MiniLM cosine similarity │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │       Deterministic Ranker           │
               │ • Calibrate scores across channels   │
               │ • Exact match guarantee & pinning    │
               │ • Corroboration & attribute bonuses  │
               │ • Low-confidence noise suppression   │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │       PostGIS & Inventory Join       │
               │ • Filter: ST_DWithin(store.location) │
               │ • Filter: inventory.price & quantity │
               │ • Order by: Nearest store distance   │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
                     Structured JSON API Response
               [Products, Nearby Stores, Prices, Distances]
```

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | Python 3.11+ / 3.14, FastAPI, Uvicorn, Pydantic v2 |
| **Database & ORM** | PostgreSQL 16, SQLAlchemy 2.0 (asyncio), AsyncPG, GeoAlchemy2 |
| **Database Extensions** | **PostGIS** 3.6 (geospatial), **pgvector** 0.8.7 (vector search), **pg_trgm** (fuzzy trigram) |
| **Migrations** | Alembic (asyncpg configuration with PostGIS/pgvector compatibility) |
| **Machine Learning** | PyTorch, Sentence Transformers (`all-MiniLM-L6-v2` fine-tuned), scikit-learn, NumPy |
| **Frontend UI** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Hugeicons |
| **DevOps / Containers** | Docker & Docker Compose (custom PostGIS + pgvector multi-extension build) |
| **Testing** | Pytest, Pytest-Cov, AnyIO, HTTPX |

---

## Repository Structure

```text
ShopLens/
├── backend/
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Revision scripts (baseline & seed migrations)
│   │   └── env.py                    # Async migration engine configuration
│   ├── apis/v1/routes/               # FastAPI route controllers
│   │   ├── auth.py                   # User registration & JWT authentication
│   │   ├── inventory.py              # Store inventory operations
│   │   ├── product.py                # Catalog management
│   │   ├── search.py                 # Hyperlocal hybrid search endpoint
│   │   └── store.py                  # Store profile & registration
│   ├── core/                         # Core configuration & settings
│   ├── db/
│   │   ├── database.py               # Async SQLAlchemy engine & session factory
│   │   └── models/                   # ORM models (Product, Store, Inventory, Attribute, etc.)
│   ├── ml/semantic_search/           # Machine Learning & Semantic Retrieval
│   │   ├── datasets/                 # Validated training, validation, test CSVs
│   │   ├── models/best_model/        # Fine-tuned 384-d SentenceTransformer model
│   │   └── scripts/                  # Training & evaluation scripts (train_model.py, etc.)
│   ├── scripts/                      # Operational utilities
│   │   └── generate_product_embeddings.py  # Script to populate pgvector embeddings
│   ├── services/search_flow/         # Modular search pipeline components
│   │   ├── normalizer.py             # Query text, price, and radius extraction
│   │   ├── filter_resolver.py        # UI vs query filter precedence reconciliation
│   │   ├── keyword_search.py         # Substring & exact ILIKE retrieval
│   │   ├── fuzzy_search.py           # Trigram similarity retrieval via pg_trgm
│   │   ├── semantic_search.py        # pgvector cosine similarity retrieval
│   │   └── candidate_ranker.py       # Deterministic fusion, score calibration & ranking
│   ├── services/search_service/      # High-level search orchestration & geospatial joins
│   ├── tests/                        # 60-test end-to-end verification suite
│   ├── requirements.txt              # Backend Python dependencies
│   └── main.py                       # FastAPI entrypoint application
├── database/
│   ├── 01-init.sql                   # Database initialization: extensions, schema & indexes
│   ├── 02-seed.sql                   # Demo catalog: users, categories, stores, products, attributes
│   └── Dockerfile.pgvector           # Docker image building PostGIS 3.6 + pgvector 0.8.7
├── frontend/                         # Next.js 16 web application
├── docs/                             # Architecture diagrams & search system documentation
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

Verify that `backend/.env` contains:
```ini
DATABASE_URL=postgresql+asyncpg://shoplens:shoplens@localhost:5432/shoplens
JWT_SECRET_KEY=shoplens_super_secret_jwt_key_change_in_production_123456
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### Step 3: Start Database Services with Docker

Start PostgreSQL (equipped with PostGIS and pgvector) and pgAdmin:

```bash
docker compose up -d --build
```

- **PostgreSQL**: Port `5432` (Username: `shoplens`, Password: `shoplens`, Database: `shoplens`)
- **pgAdmin 4**: Port `5050` (Email: `admin@gmail.com`, Password: `admin`)

Verify the container is healthy:
```bash
docker ps
```
The `shoplens-postgres` container will automatically run `database/01-init.sql`, enabling the required extensions (`pg_trgm`, `postgis`, `vector`) and establishing the table schema.

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

### Step 5: Run Database Migrations (Schema & Seed Data)

Alembic manages the database schema baseline and data seeding. From the `backend` directory:

```bash
# Ensure PYTHONPATH points to the backend folder
# Windows (PowerShell): $env:PYTHONPATH="."
# Linux/macOS: export PYTHONPATH="."

# Run all migrations up to head
alembic upgrade head
```

This applies two migrations:
1. `baseline_schema`: Confirms and tracks all 12 initial tables and indexes.
2. `seed_initial_data`: Populates demo categories, stores, products, attributes, inventory, and sales records.

Verify the current migration revision:
```bash
alembic current
```

---

### Step 6: Generate Semantic Vector Embeddings

Generate and store the 384-dimensional vector embeddings in PostgreSQL for all catalog products:

```bash
# Run from the backend directory with your virtual environment active
python scripts/generate_product_embeddings.py
```
*Output: `Prepared 20/20 embeddings... Successfully regenerated 20 product embeddings.`*

> [!TIP]
> **Optional: Re-training the Semantic Model**  
> If you ever wish to re-train the Sentence Transformer on the grocery dataset triples:
> ```bash
> python ml/semantic_search/scripts/train_model.py
> ```
> This executes in ~45 seconds on CPU and saves the best model checkpoint to `backend/ml/semantic_search/models/best_model/`.

---

### Step 7: Run Backend Tests

Run the full automated test suite (60 tests covering unit tests, multi-channel ranking, filter extraction, API contract, and semantic benchmark queries):

```bash
pytest tests -v
```

Expected result:
```text
============================= 60 passed in ~12s =============================
```

---

### Step 8: Start the Backend FastAPI Server

Launch the FastAPI application with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Step 9: Setup and Run the Frontend (Next.js)

In a separate terminal, navigate to the `frontend` folder, install npm dependencies, and start the development server:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at **[http://localhost:3000](http://localhost:3000)** to interact with the ShopLens web interface.

---

## Search Engine Pipeline & Features

### 1. Multi-Channel Hybrid Retrieval
- **Keyword Retrieval**: Exact substring matching against product names and normalized names.
- **Fuzzy Matching (`pg_trgm`)**: Handles typos and misspellings (e.g., `"choclate"` -> `"Chocolate"`) using trigram similarity (threshold `0.25`).
- **Semantic Retrieval (`pgvector`)**: Converts conversational search phrases (e.g., `"something to drink"`, `"things to spread on bread"`, `"healthy breakfast"`) into dense 384-dimensional vectors using the fine-tuned MiniLM model, querying via cosine distance:
  $$\text{cosine\_distance} = 1 - \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$

### 2. Candidate Ranker (`services/search_flow/candidate_ranker.py`)
- **Score Calibration**: Normalizes raw channel outputs into comparable relevance scores in `[0.0, 1.0]`.
- **Exact Match Guarantee**: When a user inputs an exact product name, it is pinned to rank 1.
- **Corroboration Bonus**: Products retrieved across multiple channels (e.g., both keyword and semantic) receive a confidence boost.
- **Attribute Bonus**: Queries matching registered product attributes (e.g. `drinkable`, `spread`, `sweet`, `dairy-product`) receive targeted relevance bonuses.
- **Noise Suppression**: Discards low-confidence candidates with weak scores that lack cross-channel corroboration.

### 3. Hyperlocal Geospatial Filtering
- Uses PostGIS `ST_DWithin` with geography points (WGS 84 / SRID 4326) to filter stores within the user's desired radius (default: 5.0 km).
- Calculates exact geodesic distance using `ST_Distance` to order results from nearest to furthest store.

---

## Machine Learning & Evaluation

### Dataset Summary
Located in `backend/ml/semantic_search/datasets/`:
- **Training set (`train.csv`)**: 237 triples (107 unique queries)
- **Validation set (`validation.csv`)**: 60 triples (26 unique queries)
- **Test set (`test.csv`)**: 54 triples (26 unique queries)
- Zero query leakage between train, validation, and test splits.
- Schema: `query,positive_product_id,positive_product_name,negative_product_id,negative_product_name`

### Model Performance Metrics

| Metric | Baseline (`all-MiniLM-L6-v2`) | Fine-Tuned ShopLens Model | Improvement |
| :--- | :---: | :---: | :---: |
| **Recall@5** (Val) | 88.40% | **97.31%** | **+8.91%** |
| **Recall@10** (Val) | 100.0% | **100.0%** | Maintained |
| **MRR** (Mean Reciprocal Rank) | 0.9167 | **0.9436** | **+2.69%** |
| **NDCG@10** | 0.9260 | **0.9574** | **+3.14%** |

---

## API Documentation

### Product Search Endpoint

`POST /api/v1/search/products`

#### Request Payload:
```json
{
  "query": "fresh bread under 50",
  "latitude": 30.3256,
  "longitude": 78.0322,
  "radius_km": 5.0,
  "min_price": null,
  "max_price": null,
  "limit": 20
}
```

#### Response Payload:
```json
{
  "products": [
    {
      "product_id": 5,
      "product_name": "Britannia Bread",
      "category": "Bakery",
      "price": 40.0,
      "quantity": 15,
      "store_id": 1,
      "store_name": "Sharma General Store",
      "distance_km": 0.45,
      "relevance_score": 0.96
    }
  ],
  "total_results": 1,
  "applied_filters": {
    "radius_km": 5.0,
    "max_price": 50.0,
    "min_price": null
  }
}
```

---

## Git & Repository Best Practices

When committing and pushing changes:
- **Do not commit large model weights (`.safetensors`, `.bin`)**: These are excluded via `.gitignore` to keep repository size lean and prevent GitHub size warnings. The fine-tuning script (`python ml/semantic_search/scripts/train_model.py`) reproduces the weights locally in seconds.
- **Do not commit `.env`**: Always keep credentials private; use `.env.example` as the shared template.
- **Do not commit Python caches or test coverage reports**: `__pycache__/`, `.pytest_cache/`, and `htmlcov/` are ignored.
