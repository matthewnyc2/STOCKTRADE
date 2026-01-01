"""
Migration versions.

All migration classes are defined here.
"""

from database.migrations.versions.m_20241231120000_initial_schema import Migration as Migration20241231120000
from database.migrations.versions.m_20241231150000_add_template_metadata import Migration as Migration20241231150000
from database.migrations.versions.m_20241231160000_add_logic_gate import Migration as Migration20241231160000
from database.migrations.versions.m_20241231170000_add_prices_table import Migration as Migration20241231170000

__all__ = ["Migration20241231120000", "Migration20241231150000", "Migration20241231160000", "Migration20241231170000"]
