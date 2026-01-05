"""
Data Source Manager Tests
WHY: Extensible architecture for multiple APIs
"""
import pytest


def test_data_source_manager_exists():
    """WHY: Need plugin system for data sources"""
    from services.data_sources.manager import DataSourceManager
    assert DataSourceManager is not None


def test_register_data_source():
    """WHY: Must support adding new data sources"""
    from services.data_sources.manager import DataSourceManager
    manager = DataSourceManager()
    
    class MockSource:
        def get_price(self, symbol):
            return 50000.0
    
    manager.register("mock", MockSource())
    assert "mock" in manager.get_available_sources()


def test_get_price_from_multiple_sources():
    """WHY: Reliability through multiple sources"""
    from services.data_sources.manager import DataSourceManager
    manager = DataSourceManager()
    price = manager.get_price("BTCUSDT", source="binance")
    assert price is not None
