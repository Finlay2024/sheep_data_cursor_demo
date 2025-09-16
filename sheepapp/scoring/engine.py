"""Main scoring engine that coordinates filtering and ranking."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

from .filters import FilterEngine
from .ranker import RankingEngine
from ..core.models import AnalysisConfig

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Main scoring engine that coordinates the entire scoring process."""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self.filter_engine = FilterEngine(self.config)
        self.ranking_engine = RankingEngine(self.config)
        self.scoring_results = {}
    
    def score_animals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Complete scoring process for all animals."""
        logger.info(f"Starting scoring process for {len(df)} animals")
        
        # Step 1: Apply hard filters
        filtered_df, hard_filter_results = self.filter_engine.apply_hard_filters(df)
        
        # Step 2: Apply soft filters
        scored_df, soft_filter_results = self.filter_engine.apply_soft_filters(filtered_df)
        
        # Step 3: Calculate scores and rankings
        ranked_df = self.ranking_engine.calculate_scores(scored_df)
        
        # Step 4: Rank rams specifically
        ranked_rams = self.ranking_engine.rank_rams(ranked_df)
        
        # Step 5: Identify cull candidates
        cull_candidates = self.filter_engine.identify_cull_candidates(ranked_df)
        
        # Step 6: Create detailed results
        scoring_results = self.ranking_engine.create_scoring_results(ranked_df)
        
        # Compile results
        results = {
            'original_data': df,
            'filtered_data': filtered_df,
            'scored_data': ranked_df,
            'ranked_rams': ranked_rams,
            'cull_candidates': cull_candidates,
            'scoring_results': scoring_results,
            'filter_summary': self.filter_engine.get_filter_summary(hard_filter_results, soft_filter_results),
            'ranking_summary': self.ranking_engine.get_ranking_summary(ranked_df),
            'config_used': self.config.dict()
        }
        
        self.scoring_results = results
        
        logger.info("Scoring process completed")
        return results
    
    def get_top_rams(self, n: int = 10) -> pd.DataFrame:
        """Get top N rams for selection."""
        if 'ranked_rams' not in self.scoring_results:
            logger.warning("No scoring results available. Run score_animals() first.")
            return pd.DataFrame()
        
        ranked_rams = self.scoring_results['ranked_rams']
        return ranked_rams.head(n)
    
    def get_cull_recommendations(self) -> pd.DataFrame:
        """Get cull recommendations."""
        if 'cull_candidates' not in self.scoring_results:
            logger.warning("No scoring results available. Run score_animals() first.")
            return pd.DataFrame()
        
        cull_candidates = self.scoring_results['cull_candidates']
        return cull_candidates[cull_candidates['cull_recommended'] == True]
    
    def get_animal_details(self, animal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed scoring information for a specific animal."""
        if 'scoring_results' not in self.scoring_results:
            logger.warning("No scoring results available. Run score_animals() first.")
            return None
        
        for result in self.scoring_results['scoring_results']:
            if result['animal_id'] == animal_id:
                return result
        
        logger.warning(f"Animal {animal_id} not found in scoring results")
        return None
    
    def export_results(self, output_dir: str = "output") -> Dict[str, str]:
        """Export all results to files."""
        if not self.scoring_results:
            logger.warning("No scoring results available. Run score_animals() first.")
            return {}
        
        from ..io.writers import ReportWriter
        
        writer = ReportWriter(output_dir)
        exported_files = {}
        
        # Export ranked rams
        if not self.scoring_results['ranked_rams'].empty:
            ranked_rams_path = writer.write_ranked_rams(
                self.scoring_results['ranked_rams'].to_dict('records')
            )
            exported_files['ranked_rams'] = str(ranked_rams_path)
        
        # Export cull recommendations
        cull_recs = self.get_cull_recommendations()
        if not cull_recs.empty:
            cull_path = writer.write_cull_recommendations(
                cull_recs.to_dict('records')
            )
            exported_files['cull_recommendations'] = str(cull_path)
        
        # Export detailed results
        if self.scoring_results['scoring_results']:
            results_path = writer.write_json(
                self.scoring_results,
                "detailed_results"
            )
            exported_files['detailed_results'] = str(results_path)
        
        # Export HTML report
        if not self.scoring_results['ranked_rams'].empty:
            html_path = writer.write_html_report(
                self.scoring_results['ranked_rams'],
                cull_recs,
                self.scoring_results['config_used']
            )
            exported_files['html_report'] = str(html_path)
        
        logger.info(f"Exported results to {len(exported_files)} files")
        return exported_files
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the scoring process."""
        if not self.scoring_results:
            return {}
        
        summary = {
            'total_animals_processed': len(self.scoring_results['original_data']),
            'animals_after_hard_filters': len(self.scoring_results['filtered_data']),
            'total_rams_ranked': len(self.scoring_results['ranked_rams']),
            'cull_recommendations': len(self.get_cull_recommendations()),
            'retention_rate': 0,
            'filter_summary': self.scoring_results.get('filter_summary', {}),
            'ranking_summary': self.scoring_results.get('ranking_summary', {})
        }
        
        # Calculate retention rate
        if summary['total_animals_processed'] > 0:
            summary['retention_rate'] = (
                summary['animals_after_hard_filters'] / summary['total_animals_processed']
            ) * 100
        
        return summary
    
    def validate_scoring(self) -> List[str]:
        """Validate the scoring results for consistency."""
        issues = []
        
        if not self.scoring_results:
            issues.append("No scoring results available")
            return issues
        
        # Check for data consistency
        original_count = len(self.scoring_results['original_data'])
        filtered_count = len(self.scoring_results['filtered_data'])
        
        if filtered_count > original_count:
            issues.append("Filtered data has more rows than original data")
        
        # Check for reasonable score ranges
        if 'scored_data' in self.scoring_results:
            scored_data = self.scoring_results['scored_data']
            if 'composite_score' in scored_data.columns:
                scores = scored_data['composite_score']
                if scores.min() < 0 or scores.max() > 1:
                    issues.append("Composite scores outside expected range [0, 1]")
        
        # Check for ranking consistency
        if 'ranked_rams' in self.scoring_results:
            ranked_rams = self.scoring_results['ranked_rams']
            if 'rank' in ranked_rams.columns:
                ranks = ranked_rams['rank']
                if not ranks.is_monotonic_increasing:
                    issues.append("Ranks are not properly ordered")
        
        return issues
