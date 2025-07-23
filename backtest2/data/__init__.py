"""Data management module"""

from .manager_simple import DataManager
from .sources import MockDataSource

__all__ = ['DataManager', 'MockDataSource']