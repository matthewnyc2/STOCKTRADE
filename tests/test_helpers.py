"""
Test helper utilities for backend testing.
"""

import os


def reload_database_config():
    """Reload database configuration for testing and return the DATABASE_URL."""
    # Force reload of database config by setting test environment variable
    test_url = 'sqlite:///test_database.db'
    os.environ['DATABASE_URL'] = test_url
    os.environ['TESTING'] = 'true'
    return test_url
