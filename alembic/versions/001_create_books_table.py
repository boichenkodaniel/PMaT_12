"""create books table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=200), nullable=False),
        sa.Column("isbn", sa.String(length=20), nullable=False),
        sa.Column("published_year", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn"),
    )
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_books_id"), table_name="books")
    op.drop_table("books")
