"""Tests for metrics calculation."""

import pytest
import pandas as pd
import numpy as np
from datetime import date
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sheepapp.metrics import MetricsCalculator
from sheepapp.metrics.kpis import KPICalculator

class TestKPICalculator:
    """Test KPI calculation utilities."""
    
    def test_calculate_adg(self):
        """Test ADG calculation."""
        weight_start = pd.Series([20.0, 25.0, 30.0])
        weight_end = pd.Series([40.0, 50.0, 60.0])
        days = 100
        
        adg = KPICalculator.calculate_adg(weight_start, weight_end, days)
        
        expected = pd.Series([0.2, 0.25, 0.3])
        pd.testing.assert_series_equal(adg, expected)
    
    def test_calculate_weaning_rate(self):
        """Test weaning rate calculation."""
        lambs_born = pd.Series([2, 1, 0, 3])
        lambs_weaned = pd.Series([2, 1, 0, 2])
        
        weaning_rate = KPICalculator.calculate_weaning_rate(lambs_born, lambs_weaned)
        
        expected = pd.Series([1.0, 1.0, np.nan, 2/3])
        pd.testing.assert_series_equal(weaning_rate, expected, check_names=False)
    
    def test_calculate_wool_yield(self):
        """Test wool yield calculation."""
        gfw = pd.Series([5.0, 6.0, 7.0])
        yield_percent = 0.65
        
        cfw = KPICalculator.calculate_wool_yield(gfw, yield_percent)
        
        expected = pd.Series([3.25, 3.9, 4.55])
        pd.testing.assert_series_equal(cfw, expected)
    
    def test_calculate_health_score(self):
        """Test health score calculation."""
        footrot = pd.Series([1, 2, 3])
        dag = pd.Series([2, 1, 4])
        temperament = pd.Series([4, 5, 3])
        
        health_score = KPICalculator.calculate_health_score(footrot, dag, temperament)
        
        # Expected: (5-1+5-2+4)/3, (5-2+5-1+5)/3, (5-3+5-4+3)/3
        expected = pd.Series([11/3, 12/3, 6/3])
        pd.testing.assert_series_equal(health_score, expected)
    
    def test_calculate_bse_status(self):
        """Test BSE status calculation."""
        weight_300d = pd.Series([60.0, 40.0, 55.0])
        footrot_score = pd.Series([1, 3, 2])
        dag_score = pd.Series([2, 1, 3])
        temperament = pd.Series([4, 2, 5])
        
        bse_status = KPICalculator.calculate_bse_status(
            weight_300d, footrot_score, dag_score, temperament,
            min_weight=50.0, max_footrot=2, max_dag=2, min_temperament=3
        )
        
        expected = pd.Series([True, False, False])
        pd.testing.assert_series_equal(bse_status, expected)
    
    def test_calculate_percentile_rank(self):
        """Test percentile rank calculation."""
        values = pd.Series([10, 20, 30, 40, 50])
        
        percentiles = KPICalculator.calculate_percentile_rank(values)
        
        # Should be 20, 40, 60, 80, 100
        expected = pd.Series([20, 40, 60, 80, 100])
        pd.testing.assert_series_equal(percentiles, expected)
    
    def test_calculate_zscore(self):
        """Test z-score calculation."""
        values = pd.Series([1, 2, 3, 4, 5])
        
        zscores = KPICalculator.calculate_zscore(values)
        
        # Mean = 3, Std = sqrt(2), so z-scores should be [-sqrt(2), -sqrt(2)/2, 0, sqrt(2)/2, sqrt(2)]
        mean_val = values.mean()
        std_val = values.std()
        expected = (values - mean_val) / std_val
        
        pd.testing.assert_series_equal(zscores, expected)

class TestMetricsCalculator:
    """Test main metrics calculator."""
    
    def test_calculate_growth_metrics(self):
        """Test growth metrics calculation."""
        data = {
            'animal_id': ['A001', 'A002'],
            'wt_100d': [25.0, 30.0],
            'wt_200d': [45.0, 50.0],
            'wt_300d': [65.0, 70.0],
            'wt_birth': [5.0, 6.0],
            'birth_date': [date(2023, 1, 1), date(2023, 1, 1)]
        }
        df = pd.DataFrame(data)
        
        calculator = MetricsCalculator()
        result_df = calculator._calculate_growth_metrics(df)
        
        assert 'adg_100_200d' in result_df.columns
        assert 'adg_200_300d' in result_df.columns
        assert 'adg_birth_200d' in result_df.columns
        
        # Check ADG calculations
        expected_adg_100_200d = (45.0 - 25.0) / 100  # 0.2
        assert abs(result_df['adg_100_200d'].iloc[0] - expected_adg_100_200d) < 0.001
    
    def test_calculate_wool_metrics(self):
        """Test wool metrics calculation."""
        data = {
            'animal_id': ['A001', 'A002'],
            'gfw': [5.0, 6.0],
            'micron': [20.0, 18.0],
            'staple_len': [90.0, 95.0]
        }
        df = pd.DataFrame(data)
        
        calculator = MetricsCalculator()
        result_df = calculator._calculate_wool_metrics(df)
        
        assert 'cfw' in result_df.columns
        assert 'micron_score' in result_df.columns
        assert 'staple_len_score' in result_df.columns
        
        # Check CFW calculation (65% yield)
        expected_cfw = 5.0 * 0.65
        assert abs(result_df['cfw'].iloc[0] - expected_cfw) < 0.001
    
    def test_calculate_reproduction_metrics(self):
        """Test reproduction metrics calculation."""
        data = {
            'animal_id': ['A001', 'A002'],
            'lambs_born': [2, 1],
            'lambs_weaned': [2, 1],
            'preg_scan': [1.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        calculator = MetricsCalculator()
        result_df = calculator._calculate_reproduction_metrics(df)
        
        assert 'weaning_rate' in result_df.columns
        assert 'pregnancy_success' in result_df.columns
        assert 'reproductive_efficiency' in result_df.columns
        
        # Check weaning rate calculation
        expected_weaning_rate = 2.0 / 2.0  # 1.0
        assert abs(result_df['weaning_rate'].iloc[0] - expected_weaning_rate) < 0.001
    
    def test_calculate_health_metrics(self):
        """Test health metrics calculation."""
        data = {
            'animal_id': ['A001', 'A002'],
            'fec_count': [100, 200],
            'footrot_score': [1, 2],
            'dag_score': [2, 1],
            'temperament': [4, 5]
        }
        df = pd.DataFrame(data)
        
        calculator = MetricsCalculator()
        result_df = calculator._calculate_health_metrics(df)
        
        assert 'fec_score' in result_df.columns
        assert 'health_score' in result_df.columns
        assert 'temperament_score' in result_df.columns
        
        # Check FEC score (inverted)
        expected_fec_score = 1 / (100 + 1)  # 1/101
        assert abs(result_df['fec_score'].iloc[0] - expected_fec_score) < 0.001
    
    def test_calculate_bse_status(self):
        """Test BSE status calculation."""
        data = {
            'animal_id': ['A001', 'A002'],
            'wt_300d': [60.0, 40.0],
            'footrot_score': [1, 3],
            'dag_score': [2, 1],
            'temperament': [4, 2]
        }
        df = pd.DataFrame(data)
        
        calculator = MetricsCalculator()
        result_df = calculator._calculate_bse_status(df)
        
        assert 'bse_pass' in result_df.columns
        
        # A001 should pass (weight >= 50, footrot <= 2, dag <= 2, temperament >= 3)
        # A002 should fail (weight < 50)
        assert result_df['bse_pass'].iloc[0] == True
        assert result_df['bse_pass'].iloc[1] == False
