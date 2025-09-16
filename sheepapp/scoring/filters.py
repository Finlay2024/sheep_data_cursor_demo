"""Filtering engine for sheep data analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.models import AnalysisConfig

logger = logging.getLogger(__name__)

class FilterEngine:
    """Handles hard and soft filtering of sheep data."""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self.filter_results = {}
    
    def apply_hard_filters(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply hard filters that eliminate animals from consideration."""
        logger.info("Applying hard filters")
        
        original_count = len(df)
        filtered_df = df.copy()
        filter_results = {
            'original_count': original_count,
            'filters_applied': [],
            'animals_removed': {},
            'final_count': 0
        }
        
        # Birth weight filter
        if 'wt_birth' in df.columns:
            min_birth_weight = self.config.min_birth_weight
            birth_weight_mask = df['wt_birth'] >= min_birth_weight
            removed_count = (~birth_weight_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('min_birth_weight')
                filter_results['animals_removed']['min_birth_weight'] = int(removed_count)
                filtered_df = filtered_df[birth_weight_mask]
        
        # Footrot score filter
        if 'footrot_score' in df.columns:
            max_footrot = self.config.max_footrot_score
            footrot_mask = df['footrot_score'] <= max_footrot
            removed_count = (~footrot_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('max_footrot_score')
                filter_results['animals_removed']['max_footrot_score'] = int(removed_count)
                filtered_df = filtered_df[footrot_mask]
        
        # DAG score filter
        if 'dag_score' in df.columns:
            max_dag = self.config.max_dag_score
            dag_mask = df['dag_score'] <= max_dag
            removed_count = (~dag_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('max_dag_score')
                filter_results['animals_removed']['max_dag_score'] = int(removed_count)
                filtered_df = filtered_df[dag_mask]
        
        # Weaning weight filter
        if 'wt_wean' in df.columns:
            min_weaning_weight = self.config.min_weaning_weight
            weaning_mask = df['wt_wean'] >= min_weaning_weight
            removed_count = (~weaning_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('min_weaning_weight')
                filter_results['animals_removed']['min_weaning_weight'] = int(removed_count)
                filtered_df = filtered_df[weaning_mask]
        
        # Micron filter
        if 'micron' in df.columns:
            max_micron = self.config.max_micron
            micron_mask = df['micron'] <= max_micron
            removed_count = (~micron_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('max_micron')
                filter_results['animals_removed']['max_micron'] = int(removed_count)
                filtered_df = filtered_df[micron_mask]
        
        # BSE pass filter
        if self.config.bse_pass_required and 'bse_pass' in df.columns:
            bse_mask = df['bse_pass'] == True
            removed_count = (~bse_mask).sum()
            
            if removed_count > 0:
                filter_results['filters_applied'].append('bse_pass_required')
                filter_results['animals_removed']['bse_pass_required'] = int(removed_count)
                filtered_df = filtered_df[bse_mask]
        
        filter_results['final_count'] = len(filtered_df)
        filter_results['total_removed'] = original_count - len(filtered_df)
        
        logger.info(f"Hard filters applied: {len(filter_results['filters_applied'])} filters, "
                   f"{filter_results['total_removed']} animals removed")
        
        return filtered_df, filter_results
    
    def apply_soft_filters(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply soft filters that flag animals but don't eliminate them."""
        logger.info("Applying soft filters")
        
        soft_filter_results = {
            'animals_flagged': {},
            'flags_applied': []
        }
        
        # Add soft filter columns
        filtered_df = df.copy()
        
        # 200d weight soft filter
        if 'wt_200d' in df.columns:
            min_200d_weight = getattr(self.config, 'min_200d_weight', 40.0)
            filtered_df['soft_filter_200d'] = df['wt_200d'] < min_200d_weight
            flagged_count = filtered_df['soft_filter_200d'].sum()
            
            if flagged_count > 0:
                soft_filter_results['flags_applied'].append('min_200d_weight')
                soft_filter_results['animals_flagged']['min_200d_weight'] = int(flagged_count)
        
        # 300d weight soft filter
        if 'wt_300d' in df.columns:
            min_300d_weight = getattr(self.config, 'min_300d_weight', 50.0)
            filtered_df['soft_filter_300d'] = df['wt_300d'] < min_300d_weight
            flagged_count = filtered_df['soft_filter_300d'].sum()
            
            if flagged_count > 0:
                soft_filter_results['flags_applied'].append('min_300d_weight')
                soft_filter_results['animals_flagged']['min_300d_weight'] = int(flagged_count)
        
        # Weaning rate soft filter
        if 'weaning_rate' in df.columns:
            min_weaning_rate = getattr(self.config, 'min_weaning_rate', 0.5)
            filtered_df['soft_filter_weaning'] = df['weaning_rate'] < min_weaning_rate
            flagged_count = filtered_df['soft_filter_weaning'].sum()
            
            if flagged_count > 0:
                soft_filter_results['flags_applied'].append('min_weaning_rate')
                soft_filter_results['animals_flagged']['min_weaning_rate'] = int(flagged_count)
        
        logger.info(f"Soft filters applied: {len(soft_filter_results['flags_applied'])} flags")
        
        return filtered_df, soft_filter_results
    
    def get_filter_summary(self, hard_results: Dict[str, Any], 
                          soft_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive filter summary."""
        return {
            'hard_filters': hard_results,
            'soft_filters': soft_results,
            'summary': {
                'total_hard_filters': len(hard_results.get('filters_applied', [])),
                'total_soft_filters': len(soft_results.get('flags_applied', [])),
                'animals_removed': hard_results.get('total_removed', 0),
                'animals_flagged': sum(soft_results.get('animals_flagged', {}).values())
            }
        }
    
    def identify_cull_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify animals that should be considered for culling."""
        cull_candidates = df.copy()
        
        # Add cull recommendation column
        cull_candidates['cull_recommended'] = False
        cull_candidates['cull_reasons'] = ''
        
        # Check for existing cull flags
        if 'cull_flag' in df.columns:
            existing_culls = df['cull_flag'] == 1
            cull_candidates.loc[existing_culls, 'cull_recommended'] = True
            cull_candidates.loc[existing_culls, 'cull_reasons'] = 'Existing cull flag'
        
        # Check for poor performance indicators
        cull_reasons = []
        
        # Low weights
        if 'wt_300d' in df.columns:
            low_weight_threshold = df['wt_300d'].quantile(0.1)  # Bottom 10%
            low_weight = df['wt_300d'] < low_weight_threshold
            cull_candidates.loc[low_weight, 'cull_recommended'] = True
            cull_candidates.loc[low_weight, 'cull_reasons'] += 'Low 300d weight; '
        
        # Poor health
        if 'health_score' in df.columns:
            poor_health_threshold = df['health_score'].quantile(0.1)  # Bottom 10%
            poor_health = df['health_score'] < poor_health_threshold
            cull_candidates.loc[poor_health, 'cull_recommended'] = True
            cull_candidates.loc[poor_health, 'cull_reasons'] += 'Poor health; '
        
        # Poor reproduction
        if 'weaning_rate' in df.columns:
            poor_repro = df['weaning_rate'] < 0.5
            cull_candidates.loc[poor_repro, 'cull_recommended'] = True
            cull_candidates.loc[poor_repro, 'cull_reasons'] += 'Poor reproduction; '
        
        # Clean up reasons
        cull_candidates['cull_reasons'] = cull_candidates['cull_reasons'].str.rstrip('; ')
        
        return cull_candidates
