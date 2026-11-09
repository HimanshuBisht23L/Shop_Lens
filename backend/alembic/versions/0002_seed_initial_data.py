"""seed_initial_data

Revision ID: 0002_seed_initial_data
Revises: 0001_baseline_schema
Create Date: 2026-11-09 21:05:00.000000

"""
from pathlib import Path
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_seed_initial_data'
down_revision: Union[str, Sequence[str], None] = '0001_baseline_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial demo data from 02-seed.sql."""
    seed_path = Path(__file__).resolve().parents[3] / "database" / "02-seed.sql"
    if not seed_path.exists():
        seed_path = Path("database/02-seed.sql").resolve()

    with open(seed_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Omit any trailing verification queries
    seed_body = sql.split("-- VERIFICATION")[0]

    # Remove transaction controls since Alembic wraps migrations in transactions
    seed_body = re.sub(r"^\s*(BEGIN|COMMIT);\s*$", "", seed_body, flags=re.MULTILINE)

    # Split into individual SQL statements for asyncpg compatibility
    raw_stmts = [s.strip() for s in seed_body.split(";") if s.strip()]

    for stmt in raw_stmts:
        if stmt:
            op.execute(sa.text(stmt))


def downgrade() -> None:
    """Truncate seeded demo data and reset sequences."""
    op.execute(sa.text("""
        TRUNCATE TABLE 
            sale_items,
            sales,
            predictions,
            inventory_uploads,
            inventory,
            products,
            sub_categories,
            stores,
            categories,
            search_history,
            users
        RESTART IDENTITY CASCADE;
    """))
