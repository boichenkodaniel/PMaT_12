
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_authors_id"), "authors", ["id"], unique=False)

    op.add_column("books", sa.Column("author_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_books_author_id_authors"),
        "books", "authors",
        ["author_id"], ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)
    op.create_index(op.f("ix_books_author_id"), "books", ["author_id"], unique=False)

    op.execute(text("""
        INSERT INTO authors (name, bio)
        SELECT DISTINCT author, NULL FROM books
    """))

    op.execute(text("""
        UPDATE books
        SET author_id = authors.id
        FROM authors
        WHERE books.author = authors.name
    """))

    op.alter_column("books", "author_id", nullable=False)

    op.drop_column("books", "author")


def downgrade() -> None:
    op.add_column("books", sa.Column("author", sa.String(length=200), nullable=False))

    op.execute(text("""
        UPDATE books
        SET author = authors.name
        FROM authors
        WHERE books.author_id = authors.id
    """))

    op.drop_constraint(op.f("fk_books_author_id_authors"), "books", type_="foreignkey")
    op.drop_index(op.f("ix_books_author_id"), table_name="books")
    op.drop_index(op.f("ix_books_title"), table_name="books")

    op.drop_column("books", "author_id")

    op.drop_index(op.f("ix_authors_id"), table_name="authors")
    op.drop_table("authors")
