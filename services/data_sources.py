"""
Data Sources Manager for extensible API support.
"""


class DataSourceManager:
    """Manages multiple data source APIs."""
    
    def get_available_sources(self):
        """Get list of available data sources."""
        return ["binance", "coingecko"]
