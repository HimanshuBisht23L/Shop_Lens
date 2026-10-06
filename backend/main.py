from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine
from apis.v1.routes.auth import router as auth_router
from apis.v1.routes.store import router as store_router
from apis.v1.routes.product import router as product_router
from apis.v1.routes.inventory import router as inventory_router
from apis.v1.routes.search import router as search_router

from db.models import (
    User,
    Category,
    Store,
    Product,
    Inventory,
    Sale,
    SaleItem,
    InventoryUpload,
    SearchHistory,
    Prediction,
)


app = FastAPI(
    title="ShopLens API",
    description="API for the ShopLens application",
    version="1.0.0",
)


# Auth Routes
app.include_router(
    auth_router,
    prefix="/api/v1",
)


# Store Routes
app.include_router(
    store_router,
    prefix="/api/v1",
)


# Product Routes
app.include_router(
    product_router,
    prefix="/api/v1",
)


# Inventory Routes
app.include_router(
    inventory_router,
    prefix="/api/v1",
)

# Search Routes
app.include_router(
    search_router,
    prefix="/api/v1",
)


# Root Routes
@app.get("/")
async def root():
    return {
        "message": "ShopLens API is running"
    }


# Health Check Routes
@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.get("/health/db")
async def database_health():
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT 1")
        )

        return {
            "database": "connected",
            "result": result.scalar(),
        }
    

@app.get("/test/user")
async def test_user_model():
    return {
        "model1": User.__tablename__,
        "model2": Category.__tablename__,
        "model3": Store.__tablename__,
        "model4": Product.__tablename__,
        "model5": Inventory.__tablename__,
        "model6": Sale.__tablename__,
        "model7": SaleItem.__tablename__,
        "model8": InventoryUpload.__tablename__,
        "model9": SearchHistory.__tablename__,
        "model10": Prediction.__tablename__,
    }
