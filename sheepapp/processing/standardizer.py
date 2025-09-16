"""Data standardization and normalization."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class DataStandardizer:
    """Standardizes data for analysis and comparison."""
    
    def __init__(self, method: str = "percentile"):
        self.method = method
        self.normalization_params = {}
    
    def standardize_data(self, df: pd.DataFrame, 
                        contemporary_groups: Optional[List[str]] = None) -> pd.DataFrame:
        """Standardize data within contemporary groups."""
        logger.info(f"Standardizing data using {self.method} method")
        
        standardized_df = df.copy()
        
        if contemporary_groups is None:
            contemporary_groups = df['contemporary_group'].unique()
        
        # Standardize each contemporary group separately
        for group in contemporary_groups:
            if pd.isna(group):
                continue
                
            group_mask = df['contemporary_group'] == group
            group_data = df[group_mask]
            
            if len(group_data) < 2:  # Need at least 2 animals for standardization
                logger.warning(f"Skipping standardization for group {group} (too few animals)")
                continue
            
            # Standardize traits within group
            standardized_group = self._standardize_group(group_data)
            standardized_df.loc[group_mask, standardized_group.columns] = standardized_group
        
        return standardized_df
    
    def _standardize_group(self, group_df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data within a single contemporary group."""
        standardized = group_df.copy()
        
        # Define traits to standardize
        traits = {
            'growth': ['wt_200d', 'wt_300d', 'adg_100_200d', 'adg_200_300d'],
            'wool': ['gfw', 'cfw', 'micron', 'staple_len'],
            'reproduction': ['weaning_rate', 'lambs_weaned'],
            'health': ['fec_count', 'footrot_score', 'dag_score'],
            'temperament': ['temperament']
        }
        
        for category, trait_list in traits.items():
            for trait in trait_list:
                if trait in group_df.columns:
                    standardized[f"{trait}_std"] = self._standardize_trait(
                        group_df[trait], trait, group_df['contemporary_group'].iloc[0]
                    )
        
        return standardized
    
    def _standardize_trait(self, values: pd.Series, trait: str, group: str) -> pd.Series:
        """Standardize a single trait within a group."""
        # Remove NaN values for calculation
        valid_values = values.dropna()
        
        if len(valid_values) < 2:
            return pd.Series([np.nan] * len(values), index=values.index)
        
        if self.method == "percentile":
            return self._percentile_standardize(values, valid_values)
        elif self.method == "zscore":
            return self._zscore_standardize(values, valid_values)
        else:
            raise ValueError(f"Unknown standardization method: {self.method}")
    
    def _percentile_standardize(self, values: pd.Series, valid_values: pd.Series) -> pd.Series:
        """Standardize using percentile ranking (0-100 scale)."""
        # Calculate percentiles for valid values
        percentiles = valid_values.rank(pct=True) * 100
        
        # Create mapping for all values
        result = pd.Series([np.nan] * len(values), index=values.index)
        
        for idx, val in values.items():
            if not pd.isna(val):
                # Find percentile rank
                percentile = (valid_values <= val).sum() / len(valid_values) * 100
                result.loc[idx] = percentile
        
        return result
    
    def _zscore_standardize(self, values: pd.Series, valid_values: pd.Series) -> pd.Series:
        """Standardize using z-score normalization."""
        mean_val = valid_values.mean()
        std_val = valid_values.std()
        
        if std_val == 0:
            return pd.Series([0] * len(values), index=values.index)
        
        z_scores = (values - mean_val) / std_val
        return z_scores
    
    def calculate_composite_scores(self, df: pd.DataFrame, 
                                 weights: Dict[str, float]) -> pd.DataFrame:
        """Calculate composite scores for each category."""
        logger.info("Calculating composite scores")
        
        result_df = df.copy()
        
        # Define trait categories and their weights
        trait_categories = {
            'growth': ['wt_200d_std', 'wt_300d_std', 'adg_100_200d_std', 'adg_200_300d_std'],
            'wool': ['gfw_std', 'cfw_std', 'micron_std', 'staple_len_std'],
            'reproduction': ['weaning_rate_std', 'lambs_weaned_std'],
            'health': ['fec_count_std', 'footrot_score_std', 'dag_score_std'],
            'temperament': ['temperament_std']
        }
        
        # Calculate category scores
        for category, traits in trait_categories.items():
            if category in weights:
                category_score = self._calculate_category_score(df, traits, category)
                result_df[f"{category}_score"] = category_score
        
        # Calculate overall composite score
        overall_score = self._calculate_overall_score(result_df, weights)
        result_df['composite_score'] = overall_score
        
        return result_df
    
    def _calculate_category_score(self, df: pd.DataFrame, traits: List[str], 
                                category: str) -> pd.Series:
        """Calculate score for a trait category."""
        # Get available traits
        available_traits = [t for t in traits if t in df.columns]
        
        if not available_traits:
            return pd.Series([0] * len(df), index=df.index)
        
        # Calculate mean of standardized traits
        trait_values = df[available_traits]
        
        # Handle missing values by taking mean of available traits
        category_scores = trait_values.mean(axis=1, skipna=True)
        
        # Fill any remaining NaN with 0
        category_scores = category_scores.fillna(0)
        
        return category_scores
    
    def _calculate_overall_score(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
        """Calculate overall composite score."""
        category_scores = []
        category_weights = []
        
        for category, weight in weights.items():
            score_col = f"{category}_score"
            if score_col in df.columns:
                category_scores.append(df[score_col])
                category_weights.append(weight)
        
        if not category_scores:
            return pd.Series([0] * len(df), index=df.index)
        
        # Weighted average of category scores
        weighted_scores = pd.DataFrame(category_scores).T
        weighted_scores = weighted_scores.multiply(category_weights, axis=1)
        
        overall_score = weighted_scores.sum(axis=1)
        
        return overall_score
    
    def get_standardization_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of standardization results."""
        summary = {
            'method': self.method,
            'contemporary_groups': df['contemporary_group'].nunique(),
            'standardized_traits': [],
            'score_ranges': {}
        }
        
        # Find standardized traits
        std_cols = [col for col in df.columns if col.endswith('_std')]
        summary['standardized_traits'] = std_cols
        
        # Get score ranges
        score_cols = [col for col in df.columns if col.endswith('_score')]
        for col in score_cols:
            if col in df.columns:
                summary['score_ranges'][col] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'std': df[col].std()
                }
        
        return summary
