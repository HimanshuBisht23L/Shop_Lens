"""seed_initial_data

Revision ID: 47ec0b9574d3
Revises: f4d4a8b37a8f
Create Date: 2026-11-06 13:07:30.460403

"""
from pathlib import Path
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47ec0b9574d3'
down_revision: Union[str, Sequence[str], None] = 'f4d4a8b37a8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial demo data from 02-seed.sql."""
    seed_path = Path(__file__).resolve().parents[3] / "database" / "02-seed.sql"
    if not seed_path.exists():
        seed_path = Path("database/02-seed.sql").resolve()

    with open(seed_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Omit the trailing verification queries
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
            product_attributes,
            products,
            attributes,
            stores,
            categories,
            search_history,
            users
        RESTART IDENTITY CASCADE;
    """))
