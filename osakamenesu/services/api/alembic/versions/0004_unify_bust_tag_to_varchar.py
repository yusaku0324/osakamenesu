from alembic import op
import sqlalchemy as sa


revision = '0004_unify_bust_tag_to_varchar'
down_revision = '0003_extend_bust_tag_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Detect if column type is the ENUM 'bust_tag'; if so, cast to VARCHAR(16)
    try:
        res = bind.execute(sa.text(
            """
            SELECT 1
            FROM information_schema.columns c
            JOIN pg_type t ON t.oid = (
                SELECT a.atttypid FROM pg_attribute a
                WHERE a.attrelid = (quote_ident(c.table_schema)||'.'||quote_ident(c.table_name))::regclass
                  AND a.attname = c.column_name AND a.attnum > 0 AND NOT a.attisdropped
                LIMIT 1
            )
            WHERE c.table_name = 'profiles' AND c.column_name = 'bust_tag' AND t.typname = 'bust_tag'
            """
        )).first()
        is_enum = bool(res)
    except Exception:
        is_enum = False
    if is_enum:
        op.execute("ALTER TABLE profiles ALTER COLUMN bust_tag TYPE VARCHAR(16) USING bust_tag::text")
        # Try to drop enum type if no longer used
        try:
            op.execute("DROP TYPE IF EXISTS bust_tag")
        except Exception:
            pass


def downgrade() -> None:
    # No-op: keeping VARCHAR is safe; restoring ENUM reliably is non-trivial
    pass

