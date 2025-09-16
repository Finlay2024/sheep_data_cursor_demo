#!/usr/bin/env python3
"""Test runner for sheep data analysis application."""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the test suite."""
    print("🧪 Running Sheep Data Analysis Test Suite")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"])
    
    # Run tests
    test_dir = Path(__file__).parent / "tests"
    
    print(f"Running tests from: {test_dir}")
    print()
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir),
            "-v",
            "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False
    
    return True

def run_smoke_test():
    """Run a quick smoke test with demo data."""
    print("\n🔥 Running Smoke Test")
    print("=" * 30)
    
    try:
        # Test demo data loading
        from sheepapp.io import load_demo_data
        df = load_demo_data()
        print(f"✅ Demo data loaded: {len(df)} rows")
        
        # Test basic processing
        from sheepapp.processing import DataCleaner, ContemporaryGrouping
        from sheepapp.metrics import MetricsCalculator
        from sheepapp.scoring import ScoringEngine
        from sheepapp.config_presets import ConfigPresets
        
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_data(df)
        print("✅ Data cleaning completed")
        
        grouper = ContemporaryGrouping()
        grouped_df = grouper.create_contemporary_groups(cleaned_df)
        print("✅ Contemporary grouping completed")
        
        calculator = MetricsCalculator()
        kpis_df = calculator.calculate_all_metrics(grouped_df)
        print("✅ KPI calculation completed")
        
        presets = ConfigPresets()
        config = presets.create_config_from_preset("balanced")
        scoring_engine = ScoringEngine(config)
        results = scoring_engine.score_animals(kpis_df)
        print("✅ Scoring and ranking completed")
        
        print(f"✅ Smoke test passed! Processed {len(df)} animals")
        return True
        
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐑 Sheep Data Analysis - Test Runner")
    print("=" * 40)
    
    # Run unit tests
    tests_passed = run_tests()
    
    # Run smoke test
    smoke_passed = run_smoke_test()
    
    print("\n" + "=" * 40)
    if tests_passed and smoke_passed:
        print("🎉 All tests passed! Application is ready to use.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Please check the output above.")
        sys.exit(1)
