"""
Data Source Manager.

Handles discovery, loading, and management of data source plugins.
"""

import importlib
import inspect
import logging
import pkgutil
from typing import Dict, List, Optional, Type, Any

from core.data_source import DataSource

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    Manages data source plugins.
    """

    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}

    def load_plugins(self, plugin_modules: List[Any]):
        """
        Load plugins from a list of modules.
        """
        self.data_sources.clear()
        for module in plugin_modules:
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, DataSource) and not inspect.isabstract(obj):
                    plugin_instance = obj()
                    self.data_sources[plugin_instance.name] = plugin_instance
                    logger.info(f"Loaded data source plugin: {plugin_instance.name}")

    def discover_plugins(self, plugin_dir: str = "services.data_sources"):
        """
        Discover and load data source plugins from the plugin directory.
        """
        plugin_modules = []
        try:
            package = importlib.import_module(plugin_dir)
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
                if is_pkg:
                    continue
                try:
                    module = importlib.import_module(f".{name}", package.__name__)
                    plugin_modules.append(module)
                except Exception as e:
                    logger.error(f"Error loading plugin {name}: {e}")
        except ImportError as e:
            logger.error(f"Could not import plugin package {plugin_dir}: {e}")
        
        self.load_plugins(plugin_modules)


    def get_data_source(self, name: str) -> Optional[DataSource]:
        """
        Get a data source by name.
        """
        return self.data_sources.get(name)

    def get_all_data_sources(self) -> List[DataSource]:
        """
        Get a list of all available data sources.
        """
        return list(self.data_sources.values())

    def get_available_source_names(self) -> List[str]:
        """
        Get a list of all available data source names.
        """
        return list(self.data_sources.keys())

# Global instance
data_source_manager = DataSourceManager()
data_source_manager.discover_plugins()
