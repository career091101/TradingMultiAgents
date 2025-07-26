#!/usr/bin/env python3
"""
Automated Backtest Workflow Script
Automates the process of running backtests through the WebUI
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from playwright.async_api import async_playwright, Page, Browser, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'backtest_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class BacktestAutomation:
    """Handles automated backtest execution through WebUI"""
    
    def __init__(self, base_url: str = "http://localhost:8501", timeout: int = 60000):
        self.base_url = base_url
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = Path("backtest_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    async def setup_browser(self) -> None:
        """Setup browser with required configurations"""
        logger.info("Setting up browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(self.timeout)
        logger.info("Browser setup completed")
        
    async def connect_to_webui(self) -> bool:
        """Connect to WebUI and handle login if needed"""
        logger.info(f"Connecting to WebUI at {self.base_url}")
        try:
            await self.page.goto(self.base_url, wait_until='networkidle')
            await self.page.wait_for_timeout(2000)  # Wait for app to initialize
            
            # Check if login is required
            if await self.page.locator('input[type="text"]').count() > 0:
                logger.info("Login required, attempting to authenticate...")
                await self.page.fill('input[type="text"]', 'user')
                await self.page.fill('input[type="password"]', 'user123')
                
                # Click login button
                login_button = self.page.locator('button:has-text("Login"), button:has-text("ログイン")')
                if await login_button.count() > 0:
                    await login_button.click()
                    await self.page.wait_for_timeout(2000)
                    logger.info("Login successful")
                    
            await self.take_screenshot("01_connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to WebUI: {str(e)}")
            await self.take_screenshot("error_connection")
            return False
            
    async def navigate_to_backtest(self) -> bool:
        """Navigate to backtest page"""
        logger.info("Navigating to backtest page...")
        try:
            # Look for backtest link in navigation
            backtest_link = self.page.locator('a:has-text("Backtest"), a:has-text("バックテスト")')
            if await backtest_link.count() > 0:
                await backtest_link.click()
            else:
                # Try sidebar navigation
                sidebar_link = self.page.locator('[data-testid="stSidebarNav"] a:has-text("Backtest")')
                if await sidebar_link.count() > 0:
                    await sidebar_link.click()
                else:
                    logger.warning("Backtest link not found in navigation")
                    return False
                    
            await self.page.wait_for_timeout(2000)
            await self.take_screenshot("02_backtest_page")
            logger.info("Successfully navigated to backtest page")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to backtest: {str(e)}")
            await self.take_screenshot("error_navigation")
            return False
            
    async def switch_to_execution_tab(self) -> bool:
        """Switch to backtest execution tab"""
        logger.info("Looking for backtest execution tab...")
        try:
            # Look for tabs
            execution_tab = self.page.locator('button[role="tab"]:has-text("実行"), button[role="tab"]:has-text("Execute"), button[role="tab"]:has-text("Run")')
            if await execution_tab.count() > 0:
                await execution_tab.click()
                await self.page.wait_for_timeout(1000)
                logger.info("Switched to execution tab")
            else:
                logger.info("No execution tab found, assuming we're on the correct page")
                
            await self.take_screenshot("03_execution_tab")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to execution tab: {str(e)}")
            return False
            
    async def execute_backtest(self) -> bool:
        """Execute the backtest"""
        logger.info("Executing backtest...")
        try:
            # Look for execute/run button
            execute_button = self.page.locator('button:has-text("Execute"), button:has-text("実行"), button:has-text("Run Backtest"), button:has-text("Start")')
            
            if await execute_button.count() == 0:
                logger.error("Execute button not found")
                await self.take_screenshot("error_no_execute_button")
                return False
                
            # Click execute button
            await execute_button.first.click()
            logger.info("Clicked execute button")
            
            # Wait for execution to start
            await self.page.wait_for_timeout(2000)
            await self.take_screenshot("04_execution_started")
            
            # Monitor execution progress
            max_wait_time = 300  # 5 minutes
            check_interval = 5   # Check every 5 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # Check for completion indicators
                if await self._is_execution_complete():
                    logger.info("Backtest execution completed")
                    await self.take_screenshot("05_execution_complete")
                    return True
                    
                # Check for errors
                if await self._has_execution_error():
                    logger.error("Execution error detected")
                    await self.take_screenshot("error_execution")
                    return False
                    
                await self.page.wait_for_timeout(check_interval * 1000)
                elapsed_time += check_interval
                logger.info(f"Waiting for completion... ({elapsed_time}s / {max_wait_time}s)")
                
            logger.warning("Execution timeout reached")
            await self.take_screenshot("error_timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute backtest: {str(e)}")
            await self.take_screenshot("error_execution_exception")
            return False
            
    async def check_logs_and_results(self) -> Tuple[bool, Dict[str, Any]]:
        """Check logs and determine if there are any issues"""
        logger.info("Checking logs and results...")
        results = {
            "status": "unknown",
            "errors": [],
            "warnings": [],
            "execution_time": None,
            "results_found": False
        }
        
        try:
            # Look for log section
            log_section = self.page.locator('div:has-text("Log"), div:has-text("ログ"), pre, code')
            if await log_section.count() > 0:
                log_content = await log_section.first.text_content()
                
                # Analyze log content
                if log_content:
                    # Check for errors
                    error_patterns = ["ERROR", "Exception", "Failed", "エラー", "失敗"]
                    for pattern in error_patterns:
                        if pattern in log_content:
                            results["errors"].append(f"Found {pattern} in logs")
                            
                    # Check for warnings
                    warning_patterns = ["WARNING", "WARN", "警告"]
                    for pattern in warning_patterns:
                        if pattern in log_content:
                            results["warnings"].append(f"Found {pattern} in logs")
                            
            # Check for results
            results_section = self.page.locator('div:has-text("Results"), div:has-text("結果")')
            if await results_section.count() > 0:
                results["results_found"] = True
                
            # Determine overall status
            if results["errors"]:
                results["status"] = "error"
                success = False
            elif results["warnings"]:
                results["status"] = "warning"
                success = True
            elif results["results_found"]:
                results["status"] = "success"
                success = True
            else:
                results["status"] = "unknown"
                success = False
                
            await self.take_screenshot("06_results_check")
            logger.info(f"Results check completed: {results['status']}")
            return success, results
            
        except Exception as e:
            logger.error(f"Failed to check logs: {str(e)}")
            results["status"] = "error"
            results["errors"].append(str(e))
            return False, results
            
    async def analyze_problems(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze problems and provide recommendations"""
        logger.info("Analyzing problems...")
        analysis = {
            "root_cause": "Unknown",
            "error_type": "Unknown",
            "recommendations": [],
            "severity": "low"
        }
        
        if results["status"] == "error":
            analysis["severity"] = "high"
            
            # Analyze error types
            for error in results["errors"]:
                if "connection" in error.lower():
                    analysis["error_type"] = "Connection Error"
                    analysis["root_cause"] = "Failed to connect to backend service"
                    analysis["recommendations"].extend([
                        "Check if backend services are running",
                        "Verify network connectivity",
                        "Check firewall settings"
                    ])
                elif "data" in error.lower():
                    analysis["error_type"] = "Data Error"
                    analysis["root_cause"] = "Invalid or missing data"
                    analysis["recommendations"].extend([
                        "Verify data sources are available",
                        "Check data format and validity",
                        "Ensure required data fields are present"
                    ])
                elif "config" in error.lower() or "setting" in error.lower():
                    analysis["error_type"] = "Configuration Error"
                    analysis["root_cause"] = "Invalid configuration settings"
                    analysis["recommendations"].extend([
                        "Review configuration parameters",
                        "Check for required settings",
                        "Validate parameter values"
                    ])
                    
        elif results["status"] == "warning":
            analysis["severity"] = "medium"
            analysis["error_type"] = "Warning"
            analysis["root_cause"] = "Non-critical issues detected"
            analysis["recommendations"].append("Review warnings for potential improvements")
            
        return analysis
        
    async def _is_execution_complete(self) -> bool:
        """Check if execution is complete"""
        complete_indicators = [
            "Complete", "完了", "Finished", "Success",
            "Results", "結果", "Done"
        ]
        
        for indicator in complete_indicators:
            if await self.page.locator(f'text="{indicator}"').count() > 0:
                return True
        return False
        
    async def _has_execution_error(self) -> bool:
        """Check if execution has errors"""
        error_indicators = [
            "Error", "エラー", "Failed", "失敗",
            "Exception", "Cannot", "Unable"
        ]
        
        for indicator in error_indicators:
            if await self.page.locator(f'text="{indicator}"').count() > 0:
                return True
        return False
        
    async def take_screenshot(self, name: str) -> None:
        """Take screenshot for documentation"""
        try:
            filename = self.screenshots_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(filename))
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {str(e)}")
            
    async def cleanup(self) -> None:
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
            
    async def generate_report(self, success: bool, results: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Generate final report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "results": results,
            "analysis": analysis
        }
        
        report_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("BACKTEST AUTOMATION SUMMARY")
        print("="*50)
        print(f"Status: {results['status'].upper()}")
        print(f"Success: {'YES' if success else 'NO'}")
        
        if not success:
            print(f"\nError Type: {analysis['error_type']}")
            print(f"Root Cause: {analysis['root_cause']}")
            print(f"Severity: {analysis['severity'].upper()}")
            print("\nRecommendations:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"  {i}. {rec}")
                
        if results['errors']:
            print("\nErrors Found:")
            for error in results['errors']:
                print(f"  - {error}")
                
        if results['warnings']:
            print("\nWarnings Found:")
            for warning in results['warnings']:
                print(f"  - {warning}")
                
        print("="*50)
        
    async def run(self) -> bool:
        """Main execution flow"""
        success = False
        try:
            # 1. Setup browser
            await self.setup_browser()
            
            # 2. Connect to WebUI
            if not await self.connect_to_webui():
                return False
                
            # 3. Navigate to backtest
            if not await self.navigate_to_backtest():
                return False
                
            # 4. Switch to execution tab
            if not await self.switch_to_execution_tab():
                return False
                
            # 5. Execute backtest
            if not await self.execute_backtest():
                return False
                
            # 6. Check logs and results
            success, results = await self.check_logs_and_results()
            
            # 7. Analyze problems if any
            analysis = await self.analyze_problems(results)
            
            # Generate report
            await self.generate_report(success, results, analysis)
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in workflow: {str(e)}")
            return False
            
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    automation = BacktestAutomation()
    
    # Run with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        logger.info(f"Attempt {attempt + 1} of {max_retries}")
        
        try:
            success = await automation.run()
            if success:
                logger.info("Backtest workflow completed successfully!")
                sys.exit(0)
            else:
                logger.warning(f"Attempt {attempt + 1} failed")
                
        except Exception as e:
            logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
            
        if attempt < max_retries - 1:
            logger.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)
            
    logger.error("All attempts failed. Please check the logs and reports.")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())