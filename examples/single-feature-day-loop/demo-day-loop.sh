#!/bin/bash
# Demo script for single feature day loop using CLI commands

set -e

echo "Amazing Async Dev - Single Feature Day Loop Demo"
echo "================================================"
echo ""

# Setup
echo "Setting up demo project..."
cd "$(dirname "$0")"
DEMO_PATH="demo-product"

mkdir -p "$DEMO_PATH/execution-packs"
mkdir -p "$DEMO_PATH/execution-results"
mkdir -p "$DEMO_PATH/reviews"
mkdir -p "$DEMO_PATH/logs"

echo "[OK] Project structure created"
echo ""

# Phase 1: plan-day
echo "PHASE 1: plan-day"
echo "=================="

# Using Python script for mock quick test
cd ../..
python -m cli.asyncdev run-day mock-quick

echo "[OK] ExecutionPack and ExecutionResult created"
echo ""

# Phase 2: review-night
echo "PHASE 2: review-night"
echo "====================="

python -m cli.asyncdev review-night generate

echo "[OK] DailyReviewPack generated"
echo ""

# Phase 3: resume-next-day
echo "PHASE 3: resume-next-day"
echo "========================"

python -m cli.asyncdev resume-next-day continue-loop --decision approve

echo "[OK] Loop continued"
echo ""

# Summary
echo "DEMO SUMMARY"
echo "============"

echo ""
echo "Generated artifacts in projects/demo-product/:"
ls -la projects/demo-product/

echo ""
echo "Day loop phases completed:"
echo "  1. plan-day    -> ExecutionPack created"
echo "  2. run-day     -> Task executed (mock)"
echo "  3. review-night -> DailyReviewPack generated"
echo "  4. resume-next-day -> Feature marked complete"

echo ""
echo "[SUCCESS] Demo complete!"