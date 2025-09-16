"""KPI calculation utilities and helpers."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class KPICalculator:
    """Utility class for calculating specific KPIs."""
    
    @staticmethod
    def calculate_adg(weight_start: pd.Series, weight_end: pd.Series, 
                     days: int) -> pd.Series:
        """Calculate Average Daily Gain between two weights."""
        if days <= 0:
            raise ValueError("Days must be positive")
        
        return (weight_end - weight_start) / days
    
    @staticmethod
    def calculate_weaning_rate(lambs_born: pd.Series, 
                              lambs_weaned: pd.Series) -> pd.Series:
        """Calculate weaning rate (lambs weaned / lambs born)."""
        return np.where(
            lambs_born > 0,
            lambs_weaned / lambs_born,
            np.nan
        )
    
    @staticmethod
    def calculate_wool_yield(gfw: pd.Series, yield_percent: float = 0.65) -> pd.Series:
        """Calculate clean fleece weight from greasy fleece weight."""
        return gfw * yield_percent
    
    @staticmethod
    def calculate_health_score(footrot: pd.Series, dag: pd.Series, 
                              temperament: Optional[pd.Series] = None) -> pd.Series:
        """Calculate composite health score."""
        # Convert to positive scale (higher is better)
        footrot_score = 5 - footrot
        dag_score = 5 - dag
        
        scores = [footrot_score, dag_score]
        
        if temperament is not None:
            scores.append(temperament)
        
        return pd.concat(scores, axis=1).mean(axis=1)
    
    @staticmethod
    def calculate_bse_status(weight_300d: pd.Series, 
                           footrot_score: pd.Series,
                           dag_score: pd.Series,
                           temperament: pd.Series,
                           min_weight: float = 50.0,
                           max_footrot: int = 2,
                           max_dag: int = 2,
                           min_temperament: int = 3) -> pd.Series:
        """Calculate BSE pass/fail status based on criteria."""
        criteria = [
            weight_300d >= min_weight,
            footrot_score <= max_footrot,
            dag_score <= max_dag,
            temperament >= min_temperament
        ]
        
        return pd.concat(criteria, axis=1).all(axis=1)
    
    @staticmethod
    def calculate_age_adjusted_weight(weight: pd.Series, 
                                    actual_age: pd.Series,
                                    target_age: int) -> pd.Series:
        """Calculate age-adjusted weight to target age."""
        # Simple linear adjustment (in practice, use more sophisticated models)
        age_diff = target_age - actual_age
        daily_gain = weight / actual_age  # Assume constant daily gain
        adjusted_weight = weight + (daily_gain * age_diff)
        
        return adjusted_weight
    
    @staticmethod
    def calculate_percentile_rank(values: pd.Series, 
                                 group_values: Optional[pd.Series] = None) -> pd.Series:
        """Calculate percentile rank within a group."""
        if group_values is None:
            group_values = values
        
        # Remove NaN values for calculation
        valid_mask = ~group_values.isna()
        if not valid_mask.any():
            return pd.Series([np.nan] * len(values), index=values.index)
        
        valid_values = group_values[valid_mask]
        
        # Calculate percentile ranks
        ranks = valid_values.rank(pct=True) * 100
        
        # Map back to original values
        result = pd.Series([np.nan] * len(values), index=values.index)
        
        for idx, val in values.items():
            if not pd.isna(val):
                # Find percentile rank
                percentile = (valid_values <= val).sum() / len(valid_values) * 100
                result.loc[idx] = percentile
        
        return result
    
    @staticmethod
    def calculate_zscore(values: pd.Series, 
                        group_values: Optional[pd.Series] = None) -> pd.Series:
        """Calculate z-score within a group."""
        if group_values is None:
            group_values = values
        
        # Remove NaN values for calculation
        valid_mask = ~group_values.isna()
        if not valid_mask.any():
            return pd.Series([np.nan] * len(values), index=values.index)
        
        valid_values = group_values[valid_mask]
        mean_val = valid_values.mean()
        std_val = valid_values.std()
        
        if std_val == 0:
            return pd.Series([0] * len(values), index=values.index)
        
        return (values - mean_val) / std_val
    
    @staticmethod
    def calculate_composite_score(trait_scores: Dict[str, pd.Series], 
                                weights: Dict[str, float]) -> pd.Series:
        """Calculate weighted composite score from trait scores."""
        if not trait_scores:
            return pd.Series([0] * len(next(iter(trait_scores.values()))), 
                           index=next(iter(trait_scores.values())).index)
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight == 0:
            return pd.Series([0] * len(next(iter(trait_scores.values()))), 
                           index=next(iter(trait_scores.values())).index)
        
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        # Calculate weighted sum
        weighted_scores = []
        for trait, score in trait_scores.items():
            if trait in normalized_weights:
                weighted_scores.append(score * normalized_weights[trait])
        
        if not weighted_scores:
            return pd.Series([0] * len(next(iter(trait_scores.values()))), 
                           index=next(iter(trait_scores.values())).index)
        
        return pd.concat(weighted_scores, axis=1).sum(axis=1)
    
    @staticmethod
    def get_metric_statistics(df: pd.DataFrame, 
                            metric_cols: List[str]) -> Dict[str, Dict[str, float]]:
        """Get descriptive statistics for metric columns."""
        stats = {}
        
        for col in metric_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if not col_data.empty:
                    stats[col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median(),
                        'q25': col_data.quantile(0.25),
                        'q75': col_data.quantile(0.75)
                    }
                else:
                    stats[col] = {
                        'count': 0,
                        'mean': np.nan,
                        'std': np.nan,
                        'min': np.nan,
                        'max': np.nan,
                        'median': np.nan,
                        'q25': np.nan,
                        'q75': np.nan
                    }
        
        return stats
