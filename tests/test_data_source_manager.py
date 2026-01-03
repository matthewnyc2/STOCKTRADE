"""
Tests for the DataSourceManager.
"""

import unittest
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.data_source_manager import DataSourceManager, DataSource

# Dummy DataSource classes for testing
class MockDataSource1(DataSource):
    @property
    def name(self) -> str: return "mock1"
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]: return None
    async def get_historical_prices(self, symbol: str, **kwargs) -> List[Dict[str, Any]]: return []

class MockDataSource2(DataSource):
    @property
    def name(self) -> str: return "mock2"
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]: return None
    async def get_historical_prices(self, symbol: str, **kwargs) -> List[Dict[str, Any]]: return []

# A simple object to act as a module
class FakeModule:
    pass

# Create fake modules and attach the mock classes
mock_module1 = FakeModule()
mock_module1.MockDataSource1 = MockDataSource1

mock_module2 = FakeModule()
mock_module2.MockDataSource2 = MockDataSource2


class TestDataSourceManager(unittest.TestCase):
    """
    Unit tests for the DataSourceManager.
    """

    def test_plugin_loading(self):
        """
        Test that the DataSourceManager correctly loads plugins from a list of modules.
        """
        manager = DataSourceManager()
        manager.load_plugins([mock_module1, mock_module2])

        self.assertIn("mock1", manager.get_available_source_names())
        self.assertIn("mock2", manager.get_available_source_names())
        self.assertEqual(len(manager.data_sources), 2)
        
        self.assertIsInstance(manager.get_data_source("mock1"), MockDataSource1)
        self.assertIsInstance(manager.get_data_source("mock2"), MockDataSource2)
        self.assertIsNone(manager.get_data_source("nonexistent"))
        
        all_sources = manager.get_all_data_sources()
        self.assertEqual(len(all_sources), 2)


if __name__ == '__main__':
    unittest.main()
