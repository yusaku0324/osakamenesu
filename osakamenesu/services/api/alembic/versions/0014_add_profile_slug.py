"""add slug column to profiles

Revision ID: 0014_add_profile_slug
Revises: 0013_station_search_support
Create Date: 2025-10-16 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session
import unicodedata
import re


# revision identifiers, used by Alembic.
revision = "0014_add_profile_slug"
down_revision = "0013_station_search_support"
branch_labels = None
depends_on = None


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", (value or "").strip())
    if not normalized:
        return ""
    slug = re.sub(r"[^\w\-]+", "-", normalized.lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-_")
    return slug


def upgrade() -> None:
    op.add_column("profiles", sa.Column("slug", sa.String(length=160), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)

    profiles_table = sa.table(
        "profiles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
    )

    try:
        rows = session.execute(select(profiles_table.c.id, profiles_table.c.name)).all()
        used: set[str] = set()
        for profile_id, name in rows:
            base = _slugify(name)
            if not base:
                base = str(profile_id).replace("-", "")[:16]
            candidate = base
            counter = 2
            while candidate in used:
                candidate = f"{base}-{counter}"
                counter += 1
            used.add(candidate)
            session.execute(
                profiles_table.update()
                .where(profiles_table.c.id == profile_id)
                .values(slug=candidate)
            )
        session.commit()
    finally:
        session.close()

    op.create_index("ix_profiles_slug", "profiles", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_profiles_slug", table_name="profiles")
    op.drop_column("profiles", "slug")
