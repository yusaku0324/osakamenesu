from alembic import op
import sqlalchemy as sa


revision = '0002_add_height_age'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('profiles') as batch:
        batch.add_column(sa.Column('height_cm', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('age', sa.Integer(), nullable=True))
    # Optional indexes for potential queries (harmless even if unused)
    op.create_index('ix_profiles_height_cm', 'profiles', ['height_cm'], unique=False)
    op.create_index('ix_profiles_age', 'profiles', ['age'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_profiles_age', table_name='profiles')
    op.drop_index('ix_profiles_height_cm', table_name='profiles')
    with op.batch_alter_table('profiles') as batch:
        batch.drop_column('age')
        batch.drop_column('height_cm')

