"""
Add market metadata tables.

Revision ID: add_market_tables
Revises:
Create Date: 2026-01-01

This migration creates tables for:
- coins: Tradeable assets/cryptocurrencies
- exchanges: Exchange metadata and API configuration
- market_pairs: Trading pairs on exchanges
- cached_prices: Cached price data with TTL
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_market_tables'
down_revision = None  # Set this to the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Create market metadata tables."""

    # Create coins table
    op.create_table(
        'coins',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, default='crypto', index=True),
        sa.Column('base_currency', sa.String(20), nullable=True),
        sa.Column('quote_currency', sa.String(20), nullable=True),
        sa.Column('exchange', sa.String(50), nullable=True, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('coingecko_id', sa.String(100), nullable=True, index=True),
        sa.Column('coinmarketcap_id', sa.String(100), nullable=True),
        sa.Column('market_cap', sa.Numeric(20, 2), nullable=True),
        sa.Column('volume_24h', sa.Numeric(20, 2), nullable=True),
        sa.Column('circulating_supply', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_supply', sa.Numeric(20, 2), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
    )
    # Create composite indexes
    op.create_index('idx_coins_symbol_active', 'coins', ['symbol', 'is_active'])

    # Create exchanges table
    op.create_table(
        'exchanges',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(10), nullable=False, default='cex', index=True),
        sa.Column('api_endpoint', sa.Text(), nullable=True),
        sa.Column('websocket_endpoint', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('api_secret', sa.String(500), nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_second', sa.Integer(), nullable=True),
        sa.Column('supports_websocket', sa.Boolean(), default=False),
        sa.Column('supports_rest', sa.Boolean(), default=True),
        sa.Column('supports_historical', sa.Boolean(), default=False),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
    )
    op.create_index('idx_exchanges_active', 'exchanges', ['is_active'])

    # Create market_pairs table
    op.create_table(
        'market_pairs',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('exchange_id', sa.String(50), sa.ForeignKey('exchanges.id'), index=True),
        sa.Column('base_coin_id', sa.String(20), sa.ForeignKey('coins.symbol'), index=True),
        sa.Column('quote_coin_id', sa.String(20), sa.ForeignKey('coins.symbol'), index=True),
        sa.Column('symbol', sa.String(50), index=True),
        sa.Column('min_tick_size', sa.Numeric(20, 8), nullable=True),
        sa.Column('min_lot_size', sa.Numeric(20, 8), nullable=True),
        sa.Column('max_lot_size', sa.Numeric(20, 8), nullable=True),
        sa.Column('current_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('volume_24h', sa.Numeric(20, 2), nullable=True),
        sa.Column('price_change_24h_percent', sa.Numeric(10, 4), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('is_trading', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
    )
    op.create_index('idx_market_pairs_exchange', 'market_pairs', ['exchange_id', 'is_active'])
    op.create_index('idx_market_pairs_base_quote', 'market_pairs', ['base_coin_id', 'quote_coin_id'])

    # Create cached_prices table
    op.create_table(
        'cached_prices',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('symbol', sa.String(20), index=True),
        sa.Column('exchange', sa.String(50), nullable=True, index=True),
        sa.Column('price', sa.Numeric(20, 8), nullable=False),
        sa.Column('bid_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('ask_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('volume_24h', sa.Numeric(20, 2), nullable=True),
        sa.Column('price_change_24h', sa.Numeric(20, 8), nullable=True),
        sa.Column('price_change_percent_1h', sa.Numeric(10, 4), nullable=True),
        sa.Column('price_change_percent_24h', sa.Numeric(10, 4), nullable=True),
        sa.Column('price_change_percent_7d', sa.Numeric(10, 4), nullable=True),
        sa.Column('market_cap', sa.Numeric(20, 2), nullable=True),
        sa.Column('market_cap_rank', sa.Integer(), nullable=True),
        sa.Column('ttl_seconds', sa.Integer(), default=60),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
    )
    op.create_index('idx_cached_prices_symbol_exchange', 'cached_prices', ['symbol', 'exchange'])
    op.create_index('idx_cached_prices_updated', 'cached_prices', ['updated_at'])


def downgrade():
    """Drop market metadata tables."""

    # Drop in reverse order due to foreign keys
    op.drop_index('idx_cached_prices_updated', 'cached_prices')
    op.drop_index('idx_cached_prices_symbol_exchange', 'cached_prices')
    op.drop_table('cached_prices')

    op.drop_index('idx_market_pairs_base_quote', 'market_pairs')
    op.drop_index('idx_market_pairs_exchange', 'market_pairs')
    op.drop_table('market_pairs')

    op.drop_index('idx_exchanges_active', 'exchanges')
    op.drop_table('exchanges')

    op.drop_index('idx_coins_symbol_active', 'coins')
    op.drop_table('coins')
