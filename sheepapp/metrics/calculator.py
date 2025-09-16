"""Main metrics calculator for sheep data analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, timedelta
import logging

from .kpis import KPICalculator
from ..core.models import KPIs

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """Calculates all KPIs for sheep data analysis."""
    
    def __init__(self):
        self.kpi_calculator = KPICalculator()
        self.calculation_log = []
    
    def calculate_all_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all KPIs for the dataset."""
        logger.info(f"Calculating metrics for {len(df)} animals")
        
        result_df = df.copy()
        
        # Calculate growth metrics
        result_df = self._calculate_growth_metrics(result_df)
        
        # Calculate wool metrics
        result_df = self._calculate_wool_metrics(result_df)
        
        # Calculate reproduction metrics
        result_df = self._calculate_reproduction_metrics(result_df)
        
        # Calculate health metrics
        result_df = self._calculate_health_metrics(result_df)
        
        # Calculate BSE pass/fail
        result_df = self._calculate_bse_status(result_df)
        
        # Calculate age-adjusted weights
        result_df = self._calculate_age_adjusted_weights(result_df)
        
        logger.info("Metrics calculation completed")
        return result_df
    
    def _calculate_growth_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate growth-related metrics."""
        result_df = df.copy()
        
        # Average Daily Gain (ADG) calculations
        if all(col in df.columns for col in ['wt_100d', 'wt_200d']):
            # ADG from 100 to 200 days (100 days period)
            result_df['adg_100_200d'] = (df['wt_200d'] - df['wt_100d']) / 100
            self.calculation_log.append("Calculated ADG 100-200d")
        
        if all(col in df.columns for col in ['wt_200d', 'wt_300d']):
            # ADG from 200 to 300 days (100 days period)
            result_df['adg_200_300d'] = (df['wt_300d'] - df['wt_200d']) / 100
            self.calculation_log.append("Calculated ADG 200-300d")
        
        # Overall ADG from birth to 200d
        if all(col in df.columns for col in ['wt_birth', 'wt_200d', 'birth_date']):
            # Calculate age in days at 200d measurement
            # Assuming 200d measurement is taken at 200 days of age
            result_df['adg_birth_200d'] = (df['wt_200d'] - df['wt_birth']) / 200
            self.calculation_log.append("Calculated ADG birth-200d")
        
        return result_df
    
    def _calculate_wool_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate wool-related metrics."""
        result_df = df.copy()
        
        # Clean Fleece Weight (CFW) estimation from Greasy Fleece Weight (GFW)
        if 'gfw' in df.columns:
            # Typical yield is 60-70% for most sheep breeds
            # Using 65% as default, but this could be breed-specific
            result_df['cfw'] = df['gfw'] * 0.65
            self.calculation_log.append("Calculated CFW from GFW")
        
        # Wool quality metrics
        if 'micron' in df.columns:
            # Lower micron is generally better for wool quality
            # Create inverse micron score (higher is better)
            result_df['micron_score'] = 1 / (df['micron'] + 0.1)  # Add small constant to avoid division by zero
            self.calculation_log.append("Calculated micron score")
        
        if 'staple_len' in df.columns:
            # Longer staple length is generally better
            result_df['staple_len_score'] = df['staple_len']
            self.calculation_log.append("Calculated staple length score")
        
        return result_df
    
    def _calculate_reproduction_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate reproduction-related metrics."""
        result_df = df.copy()
        
        # Weaning rate (lambs weaned / lambs born)
        if all(col in df.columns for col in ['lambs_born', 'lambs_weaned']):
            # Handle division by zero
            result_df['weaning_rate'] = np.where(
                df['lambs_born'] > 0,
                df['lambs_weaned'] / df['lambs_born'],
                np.nan
            )
            self.calculation_log.append("Calculated weaning rate")
        
        # Pregnancy success rate
        if 'preg_scan' in df.columns:
            result_df['pregnancy_success'] = df['preg_scan']
            self.calculation_log.append("Calculated pregnancy success")
        
        # Reproductive efficiency (lambs weaned per ewe)
        if 'lambs_weaned' in df.columns:
            result_df['reproductive_efficiency'] = df['lambs_weaned']
            self.calculation_log.append("Calculated reproductive efficiency")
        
        return result_df
    
    def _calculate_health_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate health-related metrics."""
        result_df = df.copy()
        
        # Faecal Egg Count (FEC) - lower is better
        if 'fec_count' in df.columns:
            # Create inverse FEC score (higher is better)
            # Add 1 to avoid division by zero, then invert
            result_df['fec_score'] = 1 / (df['fec_count'] + 1)
            self.calculation_log.append("Calculated FEC score")
        
        # Health score from footrot and DAG
        health_cols = ['footrot_score', 'dag_score']
        available_health_cols = [col for col in health_cols if col in df.columns]
        
        if available_health_cols:
            # Convert to scores where higher is better (invert the scales)
            health_scores = []
            for col in available_health_cols:
                # 5 - score gives us inverted scale (0 becomes 5, 5 becomes 0)
                health_scores.append(5 - df[col])
            
            # Average health score
            result_df['health_score'] = pd.concat(health_scores, axis=1).mean(axis=1)
            self.calculation_log.append("Calculated composite health score")
        
        # Temperament score (already in correct direction)
        if 'temperament' in df.columns:
            result_df['temperament_score'] = df['temperament']
            self.calculation_log.append("Calculated temperament score")
        
        return result_df
    
    def _calculate_bse_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate BSE (Breeding Soundness Examination) pass/fail status."""
        result_df = df.copy()
        
        # BSE criteria (simplified for demo)
        bse_criteria = []
        
        # Weight criteria
        if 'wt_300d' in df.columns:
            bse_criteria.append(df['wt_300d'] >= 50)  # Minimum 300d weight
        
        # Health criteria
        if 'footrot_score' in df.columns:
            bse_criteria.append(df['footrot_score'] <= 2)  # No severe footrot
        
        if 'dag_score' in df.columns:
            bse_criteria.append(df['dag_score'] <= 2)  # No severe DAG
        
        # Temperament criteria
        if 'temperament' in df.columns:
            bse_criteria.append(df['temperament'] >= 3)  # Reasonable temperament
        
        # Combine criteria
        if bse_criteria:
            result_df['bse_pass'] = pd.concat(bse_criteria, axis=1).all(axis=1)
            self.calculation_log.append("Calculated BSE pass/fail status")
        else:
            result_df['bse_pass'] = True  # Default to pass if no criteria available
        
        return result_df
    
    def _calculate_age_adjusted_weights(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate age-adjusted weights for fair comparison."""
        result_df = df.copy()
        
        # Age adjustment factors (simplified linear model)
        # In practice, this would use more sophisticated models
        
        if 'birth_date' in df.columns and 'wt_200d' in df.columns:
            # Calculate age at 200d measurement
            # Assuming measurement was taken at exactly 200 days
            result_df['age_200d'] = 200
            
            # Simple age adjustment (could be more sophisticated)
            # Adjust to 200 days if not exactly 200 days
            result_df['wt_200d_adj'] = df['wt_200d']
            self.calculation_log.append("Calculated age-adjusted 200d weights")
        
        if 'birth_date' in df.columns and 'wt_300d' in df.columns:
            # Calculate age at 300d measurement
            result_df['age_300d'] = 300
            
            # Simple age adjustment
            result_df['wt_300d_adj'] = df['wt_300d']
            self.calculation_log.append("Calculated age-adjusted 300d weights")
        
        return result_df
    
    def get_metrics_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of calculated metrics."""
        summary = {
            'total_animals': len(df),
            'metrics_calculated': self.calculation_log,
            'metric_availability': {},
            'metric_statistics': {}
        }
        
        # Check which metrics are available
        metric_columns = [
            'adg_100_200d', 'adg_200_300d', 'adg_birth_200d',
            'cfw', 'micron_score', 'staple_len_score',
            'weaning_rate', 'pregnancy_success', 'reproductive_efficiency',
            'fec_score', 'health_score', 'temperament_score',
            'bse_pass', 'wt_200d_adj', 'wt_300d_adj'
        ]
        
        for col in metric_columns:
            if col in df.columns:
                summary['metric_availability'][col] = True
                summary['metric_statistics'][col] = {
                    'count': df[col].count(),
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
            else:
                summary['metric_availability'][col] = False
        
        return summary
    
    def validate_metrics(self, df: pd.DataFrame) -> List[str]:
        """Validate calculated metrics for reasonableness."""
        issues = []
        
        # Check ADG values
        if 'adg_100_200d' in df.columns:
            extreme_adg = df[(df['adg_100_200d'] < 0) | (df['adg_100_200d'] > 1)]
            if not extreme_adg.empty:
                issues.append(f"Extreme ADG 100-200d values: {len(extreme_adg)} animals")
        
        # Check weaning rate
        if 'weaning_rate' in df.columns:
            invalid_weaning = df[(df['weaning_rate'] < 0) | (df['weaning_rate'] > 1)]
            if not invalid_weaning.empty:
                issues.append(f"Invalid weaning rate values: {len(invalid_weaning)} animals")
        
        # Check BSE pass rate
        if 'bse_pass' in df.columns:
            bse_pass_rate = df['bse_pass'].mean()
            if bse_pass_rate < 0.5:
                issues.append(f"Low BSE pass rate: {bse_pass_rate:.1%}")
        
        return issues
