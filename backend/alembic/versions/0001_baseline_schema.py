"""baseline_schema

Revision ID: 0001_baseline_schema
Revises: 
Create Date: 2026-11-09 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pathlib import Path
import re


# revision identifiers, used by Alembic.
revision: str = '0001_baseline_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Initialize modern production schema from 01-init.sql if not already present."""
    schema_path = Path(__file__).resolve().parents[3] / "database" / "01-init.sql"
    if not schema_path.exists():
        schema_path = Path("database/01-init.sql").resolve()

    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

        sql_clean = re.sub(r"^\s*(BEGIN|COMMIT);\s*$", "", sql, flags=re.MULTILINE)
        raw_stmts = [s.strip() for s in sql_clean.split(";") if s.strip()]

        for stmt in raw_stmts:
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    """Drop all application tables."""
    op.execute(sa.text("""
        DROP TABLE IF EXISTS sale_items CASCADE;
        DROP TABLE IF EXISTS sales CASCADE;
        DROP TABLE IF EXISTS predictions CASCADE;
        DROP TABLE IF EXISTS inventory_uploads CASCADE;
        DROP TABLE IF EXISTS inventory CASCADE;
        DROP TABLE IF EXISTS search_history CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS sub_categories CASCADE;
        DROP TABLE IF EXISTS stores CASCADE;
        DROP TABLE IF EXISTS categories CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
    """))
