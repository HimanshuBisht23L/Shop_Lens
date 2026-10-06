import os
import asyncio
from logging.config import fileConfig

from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from db.database import Base

from db.models.product import Product
from db.models.users import User
from db.models.store import Store
from db.models.inventory import Inventory
from db.models.category import Category
from db.models.inventory_upload import InventoryUpload
from db.models.prediction import Prediction
from db.models.sale import Sale, SaleItem
from db.models.search_history import SearchHistory


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Alembic Config object
config = context.config

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata
target_metadata = Base.metadata



def include_object(object, name, type_, reflected, compare_to):

    # Only filter reflected database objects.
    if not reflected:
        return True

    # Ignore every reflected table that is not part of our application.
    if type_ == "table":
        application_tables = {
            "users",
            "stores",
            "categories",
            "products",
            "inventory",
            "inventory_uploads",
            "predictions",
            "sales",
            "sale_items",
            "search_history",
        }

        return name in application_tables

    # Ignore indexes belonging to tables that are not application tables.
    if type_ == "index":
        table = getattr(object, "table", None)

        if table is not None:
            application_tables = {
                "users",
                "stores",
                "categories",
                "products",
                "inventory",
                "inventory_uploads",
                "predictions",
                "sales",
                "sale_items",
                "search_history",
            }

            return table.name in application_tables

    return True



def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    """

    url = DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,

        # Important for PostGIS schemas
        include_schemas=True,

        # Ignore PostGIS system objects
        include_object=include_object,

        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()



def do_run_migrations(connection: Connection) -> None:
    """
    Configure and run migrations using an existing connection.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,

        # Important for PostGIS schemas
        include_schemas=False,

        # Ignore PostGIS system objects
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using SQLAlchemy async engine.
    """

    configuration = config.get_section(
        config.config_ini_section,
    )

    # Use the same async DATABASE_URL from .env
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    """

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()