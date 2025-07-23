#!/bin/bash

# E2E Test Runner Script for TradingAgents2

echo "========================================"
echo "E2E Test Suite for TradingAgents2"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking environment..."
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Create test results directory
mkdir -p tests/e2e/results
cd tests/e2e

echo ""
echo "========================================"
echo "Running E2E Tests"
echo "========================================"
echo ""

# Run individual test suites
echo -e "${YELLOW}1. Testing Backtest2 Improvements...${NC}"
python3 test_backtest2_improvements.py
test1_status=$?

echo ""
echo -e "${YELLOW}2. Testing Edge Cases and Errors...${NC}"
python3 test_edge_cases_and_errors.py
test2_status=$?

echo ""
echo -e "${YELLOW}3. Testing Performance Benchmarks...${NC}"
python3 test_performance_benchmarks.py
test3_status=$?

# WebUI tests require the UI to be running
echo ""
echo -e "${YELLOW}4. WebUI Integration Tests${NC}"
echo "Note: WebUI tests require the Streamlit app to be running."
echo "To run WebUI tests:"
echo "  1. Start the app: streamlit run TradingMultiAgents/streamlit_app.py"
echo "  2. Run: python3 test_webui_backtest2_integration.py"

# Run comprehensive test suite with reporting
echo ""
echo "========================================"
echo "Generating Comprehensive Test Report"
echo "========================================"
echo ""

python3 run_all_e2e_tests.py
overall_status=$?

# Move reports to results directory
mv *.md *.json results/ 2>/dev/null

# Summary
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"

if [ $test1_status -eq 0 ]; then
    echo -e "${GREEN}✅ Backtest2 Improvements: PASSED${NC}"
else
    echo -e "${RED}❌ Backtest2 Improvements: FAILED${NC}"
fi

if [ $test2_status -eq 0 ]; then
    echo -e "${GREEN}✅ Edge Cases & Errors: PASSED${NC}"
else
    echo -e "${RED}❌ Edge Cases & Errors: FAILED${NC}"
fi

if [ $test3_status -eq 0 ]; then
    echo -e "${GREEN}✅ Performance Benchmarks: PASSED${NC}"
else
    echo -e "${RED}❌ Performance Benchmarks: FAILED${NC}"
fi

echo ""
echo "Test reports saved to: tests/e2e/results/"
echo "  - e2e_test_report.md (Markdown report)"
echo "  - e2e_test_report.json (Detailed JSON)"

# Return to original directory
cd ../..

# Exit with overall status
exit $overall_status