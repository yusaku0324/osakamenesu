from alembic import op
import sqlalchemy as sa


revision = '0003_extend_bust_tag_enum'
down_revision = '0002_add_height_age'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # If an ENUM type 'bust_tag' exists, extend it; otherwise, environments
    # created from initial migration already use VARCHAR and this is a no-op.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    has_enum = False
    try:
        # Check pg_type for presence of enum type 'bust_tag' (Postgres only)
        res = bind.execute(sa.text("""
            SELECT 1 FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'bust_tag' AND t.typtype = 'e'
        """)).first()
        has_enum = bool(res)
    except Exception:
        has_enum = False
    if has_enum:
        values = ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K_PLUS']
        for v in values:
            op.execute(f"ALTER TYPE bust_tag ADD VALUE IF NOT EXISTS '{v}'")


def downgrade() -> None:
    # Enum value removal in Postgres is non-trivial; no-op for downgrade
    pass
