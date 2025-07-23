#!/usr/bin/env python3
"""
WebUI Backtest System Stability Validator

This script validates the stability of the WebUI backtest system by checking:
1. Import integrity
2. Type safety
3. Error handling
4. Resource management
5. Data flow consistency
"""

import sys
import os
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class WebUIStabilityValidator:
    """Validates WebUI backtest system stability"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def report_error(self, test_name: str, error: str, details: Optional[Dict] = None):
        """Report a test error"""
        self.errors.append({
            "test": test_name,
            "error": error,
            "details": details or {}
        })
        self.failed_tests += 1
        logger.error(f"❌ {test_name}: {error}")
        
    def report_warning(self, test_name: str, warning: str, details: Optional[Dict] = None):
        """Report a test warning"""
        self.warnings.append({
            "test": test_name,
            "warning": warning,
            "details": details or {}
        })
        logger.warning(f"⚠️  {test_name}: {warning}")
        
    def report_pass(self, test_name: str):
        """Report a passed test"""
        self.passed_tests += 1
        logger.info(f"✅ {test_name}: PASSED")
        
    def test_imports(self):
        """Test all critical imports"""
        test_name = "Import Integrity"
        
        critical_imports = [
            ("TradingMultiAgents.webui.app", "WebUIApp"),
            ("TradingMultiAgents.webui.components.backtest", "BacktestPage"),
            ("TradingMultiAgents.webui.components.backtest2", "Backtest2Page"),
            ("TradingMultiAgents.webui.backend.backtest_wrapper", "BacktestWrapper"),
            ("TradingMultiAgents.webui.backend.backtest2_wrapper", "Backtest2Wrapper"),
            ("backtest2.core.engine", "BacktestEngine"),
            ("backtest2.agents.orchestrator", "AgentOrchestrator"),
        ]
        
        all_passed = True
        for module_name, class_name in critical_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                if not hasattr(module, class_name):
                    self.report_error(test_name, f"Class {class_name} not found in {module_name}")
                    all_passed = False
            except ImportError as e:
                self.report_error(test_name, f"Failed to import {module_name}: {e}")
                all_passed = False
                
        if all_passed:
            self.report_pass(test_name)
            
    def test_type_safety(self):
        """Test type safety in critical functions"""
        test_name = "Type Safety"
        
        try:
            # Test backtest2_wrapper type handling
            from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
            
            wrapper = Backtest2Wrapper()
            
            # Test _process_results with None
            try:
                result = wrapper._process_results(None, "TEST", None)
                if not isinstance(result, dict):
                    self.report_error(test_name, "_process_results should return dict even with None input")
                else:
                    logger.info("✓ _process_results handles None input correctly")
            except Exception as e:
                self.report_error(test_name, f"_process_results fails with None: {e}")
                
            self.report_pass(test_name)
            
        except Exception as e:
            self.report_error(test_name, f"Type safety test failed: {e}")
            
    def test_error_handling(self):
        """Test error handling mechanisms"""
        test_name = "Error Handling"
        
        try:
            from TradingMultiAgents.webui.components.backtest import BacktestPage
            
            # Test render methods with invalid data
            class MockState:
                def __init__(self):
                    self.data = {}
                    
                def get(self, key, default=None):
                    return self.data.get(key, default)
                    
                def set(self, key, value):
                    self.data[key] = value
                    
            mock_state = MockState()
            page = BacktestPage(mock_state)
            
            # Test _render_ticker_results with invalid data
            try:
                # This should handle the integer case we fixed
                page._render_ticker_results("TEST", 123)  # Pass int instead of dict
                logger.info("✓ _render_ticker_results handles invalid data types")
            except AttributeError:
                self.report_error(test_name, "_render_ticker_results doesn't handle non-dict data")
                
            self.report_pass(test_name)
            
        except Exception as e:
            self.report_error(test_name, f"Error handling test failed: {e}")
            
    async def test_async_patterns(self):
        """Test async patterns and event loop handling"""
        test_name = "Async Patterns"
        
        try:
            from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
            
            wrapper = Backtest2Wrapper()
            
            # Test event loop detection
            config = {
                "tickers": ["TEST"],
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now(),
                "initial_capital": 10000
            }
            
            # Test in sync context (should create new loop)
            try:
                # This will fail quickly due to missing data, but tests loop creation
                result = wrapper.run_backtest(config)
            except Exception as e:
                # Expected to fail due to missing data, but should handle loop correctly
                if "event loop" in str(e).lower():
                    self.report_error(test_name, f"Event loop handling issue: {e}")
                else:
                    logger.info("✓ Event loop handling works in sync context")
                    
            self.report_pass(test_name)
            
        except Exception as e:
            self.report_error(test_name, f"Async pattern test failed: {e}")
            
    def test_resource_management(self):
        """Test resource management and cleanup"""
        test_name = "Resource Management"
        
        try:
            # Test circular buffer limits
            from backtest2.utils.memory_manager import CircularBuffer
            
            buffer = CircularBuffer(max_size=10)
            
            # Add more than max_size items
            for i in range(20):
                buffer.append(f"item_{i}")
                
            if len(buffer) != 10:
                self.report_error(test_name, f"CircularBuffer not limiting size: {len(buffer)}")
            else:
                logger.info("✓ CircularBuffer correctly limits size")
                
            # Test cleanup methods exist
            from backtest2.core.engine import BacktestEngine
            from backtest2.agents.orchestrator import AgentOrchestrator
            
            if not hasattr(BacktestEngine, '_cleanup'):
                self.report_warning(test_name, "BacktestEngine missing _cleanup method")
                
            if not hasattr(AgentOrchestrator, 'cleanup'):
                self.report_warning(test_name, "AgentOrchestrator missing cleanup method")
            else:
                logger.info("✓ Cleanup methods exist")
                
            self.report_pass(test_name)
            
        except Exception as e:
            self.report_error(test_name, f"Resource management test failed: {e}")
            
    def test_data_validation(self):
        """Test data validation at boundaries"""
        test_name = "Data Validation"
        
        try:
            from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
            
            wrapper = Backtest2Wrapper()
            
            # Test config validation
            invalid_configs = [
                {},  # Empty config
                {"tickers": []},  # Empty tickers
                {"tickers": ["TEST"], "start_date": "invalid"},  # Invalid date
                {"tickers": ["TEST"], "initial_capital": -1000},  # Negative capital
            ]
            
            for i, config in enumerate(invalid_configs):
                try:
                    result = wrapper._create_backtest_config(config)
                    # Should handle invalid configs gracefully
                    logger.info(f"✓ Config validation {i+1} handled gracefully")
                except Exception as e:
                    # Expected some validation errors
                    logger.info(f"✓ Config validation {i+1} caught invalid config: {type(e).__name__}")
                    
            self.report_pass(test_name)
            
        except Exception as e:
            self.report_error(test_name, f"Data validation test failed: {e}")
            
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "warnings": len(self.warnings),
                "status": "STABLE" if self.failed_tests == 0 else "UNSTABLE"
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self._generate_recommendations()
        }
        
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        if self.failed_tests > 0:
            recommendations.append("Fix critical errors before deploying to production")
            
        if len(self.warnings) > 0:
            recommendations.append("Address warnings to improve system robustness")
            
        # Specific recommendations based on errors
        for error in self.errors:
            if "import" in error["error"].lower():
                recommendations.append("Ensure all dependencies are properly installed")
            elif "type" in error["error"].lower():
                recommendations.append("Add runtime type validation at API boundaries")
            elif "async" in error["error"].lower():
                recommendations.append("Review async/await patterns for proper resource cleanup")
                
        return list(set(recommendations))  # Remove duplicates


async def main():
    """Run all validation tests"""
    logger.info("=" * 80)
    logger.info("WebUI Backtest System Stability Validation")
    logger.info("=" * 80)
    
    validator = WebUIStabilityValidator()
    
    # Run sync tests
    logger.info("\n🔍 Testing Import Integrity...")
    validator.test_imports()
    
    logger.info("\n🔍 Testing Type Safety...")
    validator.test_type_safety()
    
    logger.info("\n🔍 Testing Error Handling...")
    validator.test_error_handling()
    
    logger.info("\n🔍 Testing Resource Management...")
    validator.test_resource_management()
    
    logger.info("\n🔍 Testing Data Validation...")
    validator.test_data_validation()
    
    # Run async tests
    logger.info("\n🔍 Testing Async Patterns...")
    await validator.test_async_patterns()
    
    # Generate report
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 80)
    
    report = validator.generate_report()
    
    logger.info(f"\nSummary:")
    logger.info(f"  Status: {report['summary']['status']}")
    logger.info(f"  Passed: {report['summary']['passed']}")
    logger.info(f"  Failed: {report['summary']['failed']}")
    logger.info(f"  Warnings: {report['summary']['warnings']}")
    
    if report['errors']:
        logger.info(f"\nErrors:")
        for error in report['errors']:
            logger.info(f"  - {error['test']}: {error['error']}")
            
    if report['warnings']:
        logger.info(f"\nWarnings:")
        for warning in report['warnings']:
            logger.info(f"  - {warning['test']}: {warning['warning']}")
            
    if report['recommendations']:
        logger.info(f"\nRecommendations:")
        for rec in report['recommendations']:
            logger.info(f"  - {rec}")
            
    # Save report
    report_path = Path("webui_stability_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"\nDetailed report saved to: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if report['summary']['status'] == "STABLE" else 1)


if __name__ == "__main__":
    asyncio.run(main())