"""
Path resolution utilities for the backtesting module.

Provides centralized path management to handle different environments
and directory structures.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PathResolver:
    """Centralized path resolution for the backtest module."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize path resolver.
        
        Args:
            base_dir: Base directory for the project. If None, auto-detect.
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = self._detect_base_dir()
        
        logger.debug(f"PathResolver initialized with base_dir: {self.base_dir}")
    
    def _detect_base_dir(self) -> Path:
        """
        Auto-detect the base directory of the project.
        
        Returns:
            Path to the base directory
        """
        # Start from current file location
        current_file = Path(__file__).resolve()
        
        # Look for project root indicators
        indicators = ['.git', 'pyproject.toml', 'setup.py', 'requirements.txt']
        
        # Walk up the directory tree
        current_dir = current_file.parent
        while current_dir != current_dir.parent:
            for indicator in indicators:
                if (current_dir / indicator).exists():
                    logger.debug(f"Found project root at: {current_dir}")
                    return current_dir
            current_dir = current_dir.parent
        
        # Fallback to parent of backtest module
        fallback = current_file.parent.parent
        logger.warning(f"Could not detect project root, using fallback: {fallback}")
        return fallback
    
    def get_paths(self) -> Dict[str, Path]:
        """
        Get all relevant paths for the backtest module.
        
        Returns:
            Dictionary of path names to Path objects
        """
        paths = {
            'base_dir': self.base_dir,
            'backtest_dir': self.base_dir / 'backtest',
            'results_dir': self.base_dir / 'backtest' / 'results',
            'cache_dir': self.base_dir / 'backtest' / 'cache',
            'data_dir': self.base_dir / 'data',
            'logs_dir': self.base_dir / 'logs',
        }
        
        # TradingMultiAgents specific paths
        tradingagents_base = self.base_dir / 'TradingMultiAgents'
        if tradingagents_base.exists():
            paths.update({
                'tradingagents_dir': tradingagents_base / 'tradingagents',
                'tradingagents_data_cache': tradingagents_base / 'tradingagents' / 'dataflows' / 'data_cache',
                'tradingagents_project': tradingagents_base / 'tradingagents',
            })
        else:
            # Fallback paths
            paths.update({
                'tradingagents_dir': self.base_dir / 'tradingagents',
                'tradingagents_data_cache': self.base_dir / 'data_cache',
                'tradingagents_project': self.base_dir,
            })
        
        return paths
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        paths = self.get_paths()
        
        # Directories that should be created
        dirs_to_create = [
            'results_dir',
            'cache_dir',
            'data_dir',
            'logs_dir',
        ]
        
        for dir_name in dirs_to_create:
            dir_path = paths.get(dir_name)
            if dir_path and not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
    
    def get_config_for_tradingagents(self) -> Dict[str, str]:
        """
        Get path configuration suitable for TradingAgents.
        
        Returns:
            Dictionary with string paths for TradingAgents config
        """
        paths = self.get_paths()
        
        return {
            'project_dir': str(paths['tradingagents_project']),
            'results_dir': str(paths['results_dir']),
            'data_dir': str(paths['data_dir']),
            'data_cache_dir': str(paths['tradingagents_data_cache']),
        }
    
    @staticmethod
    def resolve_path(path: str, base_dir: Optional[Path] = None) -> Path:
        """
        Resolve a path, handling both absolute and relative paths.
        
        Args:
            path: Path string to resolve
            base_dir: Base directory for relative paths
            
        Returns:
            Resolved Path object
        """
        path_obj = Path(path)
        
        if path_obj.is_absolute():
            return path_obj
        
        if base_dir:
            return base_dir / path
        
        # Use current working directory as fallback
        return Path.cwd() / path


# Global instance for convenience
_path_resolver = None


def get_path_resolver() -> PathResolver:
    """
    Get the global PathResolver instance.
    
    Returns:
        PathResolver instance
    """
    global _path_resolver
    if _path_resolver is None:
        _path_resolver = PathResolver()
        _path_resolver.ensure_directories()
    return _path_resolver


def get_project_paths() -> Dict[str, Path]:
    """
    Get all project paths using the global resolver.
    
    Returns:
        Dictionary of path names to Path objects
    """
    return get_path_resolver().get_paths()


def get_tradingagents_config() -> Dict[str, str]:
    """
    Get path configuration for TradingAgents.
    
    Returns:
        Dictionary with string paths
    """
    return get_path_resolver().get_config_for_tradingagents()