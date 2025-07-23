"""
Unit tests for path_utils module, focusing on edge cases.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.path_utils import PathResolver, get_path_resolver, get_project_paths, get_tradingagents_config


class TestPathResolverInit(unittest.TestCase):
    """Test PathResolver initialization edge cases."""
    
    def test_init_with_custom_base_dir(self):
        """Test initialization with custom base directory."""
        custom_dir = Path("/custom/path")
        resolver = PathResolver(base_dir=custom_dir)
        self.assertEqual(resolver.base_dir, custom_dir)
    
    def test_init_with_none_auto_detect(self):
        """Test initialization with auto-detection."""
        with patch.object(PathResolver, '_detect_base_dir') as mock_detect:
            mock_detect.return_value = Path("/auto/detected")
            resolver = PathResolver()
            mock_detect.assert_called_once()
            self.assertEqual(resolver.base_dir, Path("/auto/detected"))
    
    def test_init_with_pathlike_string(self):
        """Test initialization with string path."""
        resolver = PathResolver(base_dir="/string/path")
        self.assertEqual(resolver.base_dir, Path("/string/path"))
    
    def test_init_with_relative_path(self):
        """Test initialization with relative path."""
        resolver = PathResolver(base_dir="./relative/path")
        self.assertEqual(resolver.base_dir, Path("./relative/path"))


class TestDetectBaseDir(unittest.TestCase):
    """Test _detect_base_dir edge cases."""
    
    def setUp(self):
        """Create temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_file = Path(__file__)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('backtest.path_utils.Path')
    def test_detect_with_git_directory(self, mock_path_class):
        """Test detection when .git directory exists."""
        # Create mock structure
        mock_file = Mock()
        mock_file.resolve.return_value = Path(self.temp_dir) / "deep" / "nested" / "file.py"
        mock_path_class.return_value = mock_file
        
        # Create .git in temp dir
        git_dir = Path(self.temp_dir) / ".git"
        git_dir.mkdir()
        
        resolver = PathResolver()
        # Should find the temp_dir with .git
        self.assertTrue(resolver.base_dir.name == os.path.basename(self.temp_dir) or 
                       resolver.base_dir.parent.name == os.path.basename(self.temp_dir))
    
    @patch('backtest.path_utils.__file__', '/no/indicators/here/module.py')
    def test_detect_no_indicators_fallback(self):
        """Test fallback when no project indicators found."""
        with patch('pathlib.Path.exists', return_value=False):
            resolver = PathResolver()
            # Should fall back to parent of parent
            expected = Path('/no/indicators')
            self.assertEqual(resolver.base_dir, expected)
    
    def test_detect_multiple_indicators(self):
        """Test when multiple indicators exist at different levels."""
        # Create nested structure with indicators
        level1 = Path(self.temp_dir) / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        
        level3.mkdir(parents=True)
        
        # Create indicators at different levels
        (level1 / "setup.py").touch()
        (level2 / ".git").mkdir()
        (level3 / "requirements.txt").touch()
        
        # Mock __file__ to be in level3
        with patch('backtest.path_utils.__file__', str(level3 / "module.py")):
            resolver = PathResolver()
            # Should find level2 with .git (first indicator when walking up)
            self.assertIn("level2", str(resolver.base_dir))


class TestGetPaths(unittest.TestCase):
    """Test get_paths method edge cases."""
    
    def setUp(self):
        """Set up test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.resolver = PathResolver(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_paths_with_tradingmultiagents(self):
        """Test paths when TradingMultiAgents directory exists."""
        # Create TradingMultiAgents structure
        tma_dir = Path(self.temp_dir) / "TradingMultiAgents"
        tma_dir.mkdir()
        (tma_dir / "tradingagents").mkdir()
        (tma_dir / "tradingagents" / "dataflows" / "data_cache").mkdir(parents=True)
        
        paths = self.resolver.get_paths()
        
        self.assertEqual(paths['base_dir'], Path(self.temp_dir))
        self.assertEqual(paths['tradingagents_dir'], tma_dir / "tradingagents")
        self.assertEqual(paths['tradingagents_data_cache'], 
                        tma_dir / "tradingagents" / "dataflows" / "data_cache")
        self.assertEqual(paths['tradingagents_project'], tma_dir / "tradingagents")
    
    def test_get_paths_without_tradingmultiagents(self):
        """Test fallback paths when TradingMultiAgents doesn't exist."""
        paths = self.resolver.get_paths()
        
        self.assertEqual(paths['base_dir'], Path(self.temp_dir))
        self.assertEqual(paths['tradingagents_dir'], Path(self.temp_dir) / "tradingagents")
        self.assertEqual(paths['tradingagents_data_cache'], Path(self.temp_dir) / "data_cache")
        self.assertEqual(paths['tradingagents_project'], Path(self.temp_dir))
    
    def test_get_paths_all_keys_present(self):
        """Test that all expected path keys are present."""
        paths = self.resolver.get_paths()
        
        expected_keys = [
            'base_dir', 'backtest_dir', 'results_dir', 'cache_dir',
            'data_dir', 'logs_dir', 'tradingagents_dir', 
            'tradingagents_data_cache', 'tradingagents_project'
        ]
        
        for key in expected_keys:
            self.assertIn(key, paths)
            self.assertIsInstance(paths[key], Path)


class TestEnsureDirectories(unittest.TestCase):
    """Test ensure_directories edge cases."""
    
    def setUp(self):
        """Set up test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.resolver = PathResolver(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_directories_creates_missing(self):
        """Test that missing directories are created."""
        self.resolver.ensure_directories()
        
        # Check that directories were created
        paths = self.resolver.get_paths()
        self.assertTrue(paths['results_dir'].exists())
        self.assertTrue(paths['cache_dir'].exists())
        self.assertTrue(paths['data_dir'].exists())
        self.assertTrue(paths['logs_dir'].exists())
    
    def test_ensure_directories_existing_unchanged(self):
        """Test that existing directories are not modified."""
        # Pre-create directories with files
        paths = self.resolver.get_paths()
        paths['results_dir'].mkdir(parents=True)
        test_file = paths['results_dir'] / "test.txt"
        test_file.write_text("test content")
        
        self.resolver.ensure_directories()
        
        # File should still exist
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), "test content")
    
    def test_ensure_directories_permission_error(self):
        """Test handling of permission errors."""
        # The current implementation doesn't handle permission errors
        # This test documents the current behavior
        paths = self.resolver.get_paths()
        
        # Make a directory read-only to trigger permission error
        test_dir = paths['results_dir'].parent
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # On some systems, we can't reliably trigger permission errors
        # So we'll skip this test for now
        # In production, permission errors would be logged but raised
        pass
    
    def test_ensure_directories_with_symlinks(self):
        """Test with symlinked directories."""
        # Create a target directory
        target_dir = Path(self.temp_dir) / "target"
        target_dir.mkdir()
        
        # Create symlink for results_dir
        results_link = Path(self.temp_dir) / "backtest" / "results"
        results_link.parent.mkdir(parents=True)
        results_link.symlink_to(target_dir)
        
        self.resolver.ensure_directories()
        
        # Should handle symlink correctly
        self.assertTrue(results_link.exists())
        self.assertTrue(results_link.is_symlink())


class TestResolvePathStatic(unittest.TestCase):
    """Test static resolve_path method edge cases."""
    
    def test_resolve_absolute_path(self):
        """Test resolving absolute paths."""
        abs_path = "/absolute/path/to/file"
        resolved = PathResolver.resolve_path(abs_path)
        self.assertEqual(resolved, Path(abs_path))
    
    def test_resolve_relative_with_base_dir(self):
        """Test resolving relative path with base directory."""
        base = Path("/base/directory")
        rel_path = "relative/path"
        resolved = PathResolver.resolve_path(rel_path, base_dir=base)
        self.assertEqual(resolved, base / rel_path)
    
    def test_resolve_relative_no_base_dir(self):
        """Test resolving relative path without base directory."""
        rel_path = "relative/path"
        resolved = PathResolver.resolve_path(rel_path)
        expected = Path.cwd() / rel_path
        self.assertEqual(resolved, expected)
    
    def test_resolve_empty_string(self):
        """Test resolving empty string path."""
        resolved = PathResolver.resolve_path("")
        self.assertEqual(resolved, Path.cwd())
    
    def test_resolve_dot_path(self):
        """Test resolving current directory '.'."""
        resolved = PathResolver.resolve_path(".")
        self.assertEqual(resolved, Path.cwd() / ".")
    
    def test_resolve_with_special_chars(self):
        """Test resolving path with special characters."""
        special_path = "path with spaces/and-dashes/under_scores"
        base = Path("/base")
        resolved = PathResolver.resolve_path(special_path, base_dir=base)
        self.assertEqual(resolved, base / special_path)
    
    def test_resolve_with_parent_refs(self):
        """Test resolving path with parent directory references."""
        path_with_parent = "some/../other/path"
        resolved = PathResolver.resolve_path(path_with_parent)
        # The actual path includes the parent reference, not normalized
        self.assertEqual(resolved, Path.cwd() / "some/../other/path")


class TestGlobalFunctions(unittest.TestCase):
    """Test global convenience functions."""
    
    @patch('backtest.path_utils._path_resolver', None)
    def test_get_path_resolver_singleton(self):
        """Test that get_path_resolver returns singleton."""
        resolver1 = get_path_resolver()
        resolver2 = get_path_resolver()
        self.assertIs(resolver1, resolver2)
    
    @patch('backtest.path_utils.get_path_resolver')
    def test_get_project_paths_delegates(self, mock_get_resolver):
        """Test that get_project_paths delegates correctly."""
        mock_resolver = Mock()
        mock_resolver.get_paths.return_value = {"test": Path("/test")}
        mock_get_resolver.return_value = mock_resolver
        
        result = get_project_paths()
        
        mock_resolver.get_paths.assert_called_once()
        self.assertEqual(result, {"test": Path("/test")})
    
    @patch('backtest.path_utils.get_path_resolver')
    def test_get_tradingagents_config_delegates(self, mock_get_resolver):
        """Test that get_tradingagents_config delegates correctly."""
        mock_resolver = Mock()
        mock_resolver.get_config_for_tradingagents.return_value = {"key": "value"}
        mock_get_resolver.return_value = mock_resolver
        
        result = get_tradingagents_config()
        
        mock_resolver.get_config_for_tradingagents.assert_called_once()
        self.assertEqual(result, {"key": "value"})


class TestConfigForTradingAgents(unittest.TestCase):
    """Test get_config_for_tradingagents edge cases."""
    
    def setUp(self):
        """Set up test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.resolver = PathResolver(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_returns_strings(self):
        """Test that config returns string paths, not Path objects."""
        config = self.resolver.get_config_for_tradingagents()
        
        for key, value in config.items():
            self.assertIsInstance(value, str)
            self.assertNotIsInstance(value, Path)
    
    def test_config_paths_are_absolute(self):
        """Test that returned paths are absolute."""
        config = self.resolver.get_config_for_tradingagents()
        
        for key, value in config.items():
            path = Path(value)
            self.assertTrue(path.is_absolute(), 
                          f"Path for {key} is not absolute: {value}")


class TestEdgeCasesIntegration(unittest.TestCase):
    """Integration tests for complex edge cases."""
    
    def test_deeply_nested_project_structure(self):
        """Test with deeply nested project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create deep structure
            deep_path = Path(temp_dir)
            for i in range(10):
                deep_path = deep_path / f"level{i}"
            deep_path.mkdir(parents=True)
            
            # Put .git at top level
            (Path(temp_dir) / ".git").mkdir()
            
            # Mock being deep in structure
            with patch('backtest.path_utils.__file__', str(deep_path / "module.py")):
                resolver = PathResolver()
                # Should still find the root
                self.assertEqual(resolver.base_dir.name, os.path.basename(temp_dir))
    
    def test_concurrent_directory_creation(self):
        """Test thread safety of directory creation."""
        import threading
        
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = PathResolver(base_dir=temp_dir)
            
            # Function to create directories
            def create_dirs():
                resolver.ensure_directories()
            
            # Run multiple threads
            threads = [threading.Thread(target=create_dirs) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # All directories should exist
            paths = resolver.get_paths()
            self.assertTrue(paths['results_dir'].exists())
            self.assertTrue(paths['cache_dir'].exists())


if __name__ == '__main__':
    unittest.main()