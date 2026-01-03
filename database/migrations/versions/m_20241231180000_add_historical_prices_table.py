"""
Add historical_prices table.

Revision ID: m_20241231180000
Revises: m_20241231170000
Create Date: 2025-01-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'm_20241231180000'
down_revision = 'm_20241231170000'
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply the migration.
    """
    op.create_table(
        'historical_prices',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.PrimaryKeyConstraint('symbol', 'timeframe', 'timestamp')
    )
    op.create_index(
        'idx_historical_prices_symbol_timeframe_timestamp',
        'historical_prices',
        ['symbol', 'timeframe', 'timestamp'],
        unique=False
    )


def downgrade():
    """
    Revert the migration.
    """
    op.drop_index('idx_historical_prices_symbol_timeframe_timestamp', table_name='historical_prices')
    op.drop_table('historical_prices')
