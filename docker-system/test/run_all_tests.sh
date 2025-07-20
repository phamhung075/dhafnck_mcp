#!/bin/bash
# run_all_tests.sh - Main test runner for Docker CLI system

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
TEST_DIR="$(dirname "$0")"
FAILED_TESTS=0
TOTAL_TESTS=0

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Docker CLI System Test Suite${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Find and run all test files
for test_file in "$TEST_DIR"/test_*.sh; do
    if [[ -f "$test_file" && "$test_file" != *"test_framework.sh" ]]; then
        echo -e "${YELLOW}Running: $(basename "$test_file")${NC}"
        echo "--------------------------------"
        
        # Run test and capture exit code
        bash "$test_file"
        test_exit_code=$?
        
        ((TOTAL_TESTS++))
        
        if [[ $test_exit_code -eq 0 ]]; then
            echo -e "${GREEN}✓ $(basename "$test_file") passed${NC}"
        else
            echo -e "${RED}✗ $(basename "$test_file") failed${NC}"
            ((FAILED_TESTS++))
        fi
        echo ""
    fi
done

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo "Total test suites: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$((TOTAL_TESTS - FAILED_TESTS))${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

# Exit with appropriate code
if [[ $FAILED_TESTS -gt 0 ]]; then
    echo -e "\n${RED}TEST SUITE FAILED${NC}"
    exit 1
else
    echo -e "\n${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi