"""Ranking engine for sheep data analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.models import AnalysisConfig, ScoringResult

logger = logging.getLogger(__name__)

class RankingEngine:
    """Handles ranking and scoring of sheep data."""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self.ranking_results = {}
    
    def calculate_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite scores for all animals."""
        logger.info("Calculating composite scores")
        
        scored_df = df.copy()
        
        # Calculate category scores
        scored_df = self._calculate_category_scores(scored_df)
        
        # Calculate overall composite score
        scored_df = self._calculate_composite_score(scored_df)
        
        # Add ranking
        scored_df = self._add_ranking(scored_df)
        
        logger.info("Score calculation completed")
        return scored_df
    
    def _calculate_category_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate scores for each trait category."""
        result_df = df.copy()
        
        # Growth score
        if 'growth_score' not in df.columns:
            growth_traits = ['adg_100_200d', 'adg_200_300d', 'wt_200d_adj', 'wt_300d_adj']
            available_traits = [t for t in growth_traits if t in df.columns]
            
            if available_traits:
                growth_scores = df[available_traits].mean(axis=1, skipna=True)
                result_df['growth_score'] = growth_scores.fillna(0)
            else:
                result_df['growth_score'] = 0
        
        # Wool score
        if 'wool_score' not in df.columns:
            wool_traits = ['gfw', 'cfw', 'micron_score', 'staple_len_score']
            available_traits = [t for t in wool_traits if t in df.columns]
            
            if available_traits:
                wool_scores = df[available_traits].mean(axis=1, skipna=True)
                result_df['wool_score'] = wool_scores.fillna(0)
            else:
                result_df['wool_score'] = 0
        
        # Reproduction score
        if 'reproduction_score' not in df.columns:
            repro_traits = ['weaning_rate', 'lambs_weaned', 'pregnancy_success']
            available_traits = [t for t in repro_traits if t in df.columns]
            
            if available_traits:
                repro_scores = df[available_traits].mean(axis=1, skipna=True)
                result_df['reproduction_score'] = repro_scores.fillna(0)
            else:
                result_df['reproduction_score'] = 0
        
        # Health score
        if 'health_score' not in df.columns:
            health_traits = ['fec_score', 'footrot_score', 'dag_score']
            available_traits = [t for t in health_traits if t in df.columns]
            
            if available_traits:
                # For health, we want to invert some scores (lower is better)
                health_data = df[available_traits].copy()
                
                # Invert footrot and DAG scores (5 - score)
                if 'footrot_score' in health_data.columns:
                    health_data['footrot_score'] = 5 - health_data['footrot_score']
                if 'dag_score' in health_data.columns:
                    health_data['dag_score'] = 5 - health_data['dag_score']
                
                health_scores = health_data.mean(axis=1, skipna=True)
                result_df['health_score'] = health_scores.fillna(0)
            else:
                result_df['health_score'] = 0
        
        # Temperament score
        if 'temperament_score' not in df.columns:
            if 'temperament' in df.columns:
                result_df['temperament_score'] = df['temperament'].fillna(0)
            else:
                result_df['temperament_score'] = 0
        
        return result_df
    
    def _calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate overall composite score using category weights."""
        result_df = df.copy()
        
        # Get category scores
        category_scores = {}
        weights = self.config.weights
        
        for category in weights.keys():
            score_col = f"{category}_score"
            if score_col in df.columns:
                category_scores[category] = df[score_col]
        
        if not category_scores:
            result_df['composite_score'] = 0
            return result_df
        
        # Calculate weighted average
        weighted_scores = []
        total_weight = 0
        
        for category, score in category_scores.items():
            weight = weights.get(category, 0)
            if weight > 0:
                weighted_scores.append(score * weight)
                total_weight += weight
        
        if weighted_scores and total_weight > 0:
            composite_score = pd.concat(weighted_scores, axis=1).sum(axis=1) / total_weight
        else:
            composite_score = pd.Series([0] * len(df), index=df.index)
        
        result_df['composite_score'] = composite_score
        
        return result_df
    
    def _add_ranking(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ranking based on composite score."""
        result_df = df.copy()
        
        if 'composite_score' in df.columns:
            # Rank in descending order (higher score = better rank)
            result_df['rank'] = df['composite_score'].rank(ascending=False, method='min').astype(int)
        else:
            result_df['rank'] = 1
        
        return result_df
    
    def rank_rams(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rank rams specifically for selection."""
        # Filter for rams only
        rams_df = df[df['sex'] == 'Ram'].copy()
        
        if rams_df.empty:
            logger.warning("No rams found for ranking")
            return pd.DataFrame()
        
        # Calculate scores and rank
        ranked_rams = self.calculate_scores(rams_df)
        
        # Sort by rank
        ranked_rams = ranked_rams.sort_values('rank')
        
        # Add selection recommendation
        ranked_rams['selection_recommended'] = ranked_rams['rank'] <= 10  # Top 10
        
        logger.info(f"Ranked {len(ranked_rams)} rams")
        
        return ranked_rams
    
    def create_scoring_results(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create detailed scoring results for each animal."""
        results = []
        
        for _, row in df.iterrows():
            result = {
                'animal_id': row['animal_id'],
                'sex': row['sex'],
                'final_score': row.get('composite_score', 0),
                'rank': row.get('rank', 999),
                'hard_filters_passed': True,  # Already filtered
                'hard_filters_hit': [],
                'soft_filters_passed': True,  # Will be updated by filter engine
                'soft_filters_hit': [],
                'component_scores': {
                    'growth': row.get('growth_score', 0),
                    'wool': row.get('wool_score', 0),
                    'reproduction': row.get('reproduction_score', 0),
                    'health': row.get('health_score', 0),
                    'temperament': row.get('temperament_score', 0)
                },
                'trait_scores': self._extract_trait_scores(row),
                'explanation': self._generate_explanation(row),
                'cull_recommended': row.get('cull_recommended', False),
                'cull_reason': row.get('cull_reasons', '')
            }
            
            results.append(result)
        
        return results
    
    def _extract_trait_scores(self, row: pd.Series) -> Dict[str, float]:
        """Extract individual trait scores from a row."""
        trait_scores = {}
        
        # Growth traits
        growth_traits = ['adg_100_200d', 'adg_200_300d', 'wt_200d_adj', 'wt_300d_adj']
        for trait in growth_traits:
            if trait in row:
                trait_scores[trait] = row[trait]
        
        # Wool traits
        wool_traits = ['gfw', 'cfw', 'micron_score', 'staple_len_score']
        for trait in wool_traits:
            if trait in row:
                trait_scores[trait] = row[trait]
        
        # Reproduction traits
        repro_traits = ['weaning_rate', 'lambs_weaned', 'pregnancy_success']
        for trait in repro_traits:
            if trait in row:
                trait_scores[trait] = row[trait]
        
        # Health traits
        health_traits = ['fec_score', 'footrot_score', 'dag_score']
        for trait in health_traits:
            if trait in row:
                trait_scores[trait] = row[trait]
        
        # Temperament
        if 'temperament' in row:
            trait_scores['temperament'] = row['temperament']
        
        return trait_scores
    
    def _generate_explanation(self, row: pd.Series) -> Dict[str, Any]:
        """Generate explanation for the scoring."""
        explanation = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Analyze component scores
        component_scores = {
            'growth': row.get('growth_score', 0),
            'wool': row.get('wool_score', 0),
            'reproduction': row.get('reproduction_score', 0),
            'health': row.get('health_score', 0),
            'temperament': row.get('temperament_score', 0)
        }
        
        # Find strengths and weaknesses
        for category, score in component_scores.items():
            if score > 0.7:  # High score
                explanation['strengths'].append(f"Strong {category} performance")
            elif score < 0.3:  # Low score
                explanation['weaknesses'].append(f"Poor {category} performance")
        
        # Generate recommendations
        if 'growth_score' in row and row['growth_score'] < 0.3:
            explanation['recommendations'].append("Focus on improving growth performance")
        
        if 'health_score' in row and row['health_score'] < 0.3:
            explanation['recommendations'].append("Address health issues")
        
        if 'reproduction_score' in row and row['reproduction_score'] < 0.3:
            explanation['recommendations'].append("Improve reproductive performance")
        
        return explanation
    
    def get_ranking_summary(self, ranked_df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of ranking results."""
        if ranked_df.empty:
            return {}
        
        summary = {
            'total_animals': len(ranked_df),
            'score_statistics': {
                'mean': ranked_df['composite_score'].mean(),
                'std': ranked_df['composite_score'].std(),
                'min': ranked_df['composite_score'].min(),
                'max': ranked_df['composite_score'].max()
            },
            'top_performers': ranked_df.head(10)[['animal_id', 'composite_score', 'rank']].to_dict('records'),
            'category_averages': {}
        }
        
        # Category averages
        categories = ['growth', 'wool', 'reproduction', 'health', 'temperament']
        for category in categories:
            score_col = f"{category}_score"
            if score_col in ranked_df.columns:
                summary['category_averages'][category] = ranked_df[score_col].mean()
        
        return summary
