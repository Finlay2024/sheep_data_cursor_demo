"""Contemporary grouping logic for sheep data analysis."""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ContemporaryGrouping:
    """Handles contemporary group creation and management."""
    
    def __init__(self, window_days: int = 30):
        self.window_days = window_days
        self.grouping_log = []
    
    def create_contemporary_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create contemporary groups based on management group and birth date windows."""
        logger.info(f"Creating contemporary groups for {len(df)} animals")
        
        # Add contemporary group column
        df = df.copy()
        df['contemporary_group'] = None
        
        # Group by management group first
        for mgmt_group in df['mgmt_group'].unique():
            group_df = df[df['mgmt_group'] == mgmt_group].copy()
            
            if 'birth_date' not in group_df.columns:
                logger.warning(f"No birth_date column for management group {mgmt_group}")
                continue
            
            # Create contemporary groups within management group
            contemporary_groups = self._group_by_birth_window(group_df)
            
            # Update the main dataframe
            for animal_id, cont_group in contemporary_groups.items():
                df.loc[df['animal_id'] == animal_id, 'contemporary_group'] = cont_group
        
        # Log grouping results
        group_counts = df['contemporary_group'].value_counts()
        self.grouping_log.append(f"Created {len(group_counts)} contemporary groups")
        self.grouping_log.append(f"Group sizes: {group_counts.to_dict()}")
        
        return df
    
    def _group_by_birth_window(self, group_df: pd.DataFrame) -> Dict[str, str]:
        """Group animals by birth date windows within a management group."""
        if group_df.empty or 'birth_date' not in group_df.columns:
            return {}
        
        # Sort by birth date
        group_df = group_df.sort_values('birth_date')
        
        contemporary_groups = {}
        current_group = 1
        current_group_start = None
        
        for _, row in group_df.iterrows():
            birth_date = row['birth_date']
            animal_id = row['animal_id']
            
            if current_group_start is None:
                # First animal in group
                current_group_start = birth_date
                group_name = f"{row['mgmt_group']}_G{current_group}"
            else:
                # Check if within window
                days_diff = (birth_date - current_group_start).days
                
                if days_diff <= self.window_days:
                    # Same group
                    group_name = f"{row['mgmt_group']}_G{current_group}"
                else:
                    # New group
                    current_group += 1
                    current_group_start = birth_date
                    group_name = f"{row['mgmt_group']}_G{current_group}"
            
            contemporary_groups[animal_id] = group_name
        
        return contemporary_groups
    
    def get_contemporary_group_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about contemporary groups."""
        if 'contemporary_group' not in df.columns:
            return {}
        
        stats = {}
        group_counts = df['contemporary_group'].value_counts()
        
        stats['total_groups'] = len(group_counts)
        stats['group_sizes'] = group_counts.to_dict()
        stats['min_group_size'] = group_counts.min()
        stats['max_group_size'] = group_counts.max()
        stats['avg_group_size'] = group_counts.mean()
        
        # Group size distribution
        size_dist = group_counts.value_counts().sort_index()
        stats['size_distribution'] = size_dist.to_dict()
        
        return stats
    
    def validate_contemporary_groups(self, df: pd.DataFrame) -> List[str]:
        """Validate contemporary group assignments."""
        issues = []
        
        if 'contemporary_group' not in df.columns:
            issues.append("No contemporary_group column found")
            return issues
        
        # Check for groups that are too small
        group_counts = df['contemporary_group'].value_counts()
        small_groups = group_counts[group_counts < 3]
        
        if not small_groups.empty:
            issues.append(f"Small contemporary groups (<3 animals): {small_groups.to_dict()}")
        
        # Check for groups that are too large
        large_groups = group_counts[group_counts > 50]
        if not large_groups.empty:
            issues.append(f"Large contemporary groups (>50 animals): {large_groups.to_dict()}")
        
        # Check for missing contemporary groups
        missing_groups = df['contemporary_group'].isna().sum()
        if missing_groups > 0:
            issues.append(f"Missing contemporary group assignments: {missing_groups} animals")
        
        return issues
    
    def get_animals_by_contemporary_group(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Get animals grouped by contemporary group."""
        if 'contemporary_group' not in df.columns:
            return {}
        
        return {group: group_df for group, group_df in df.groupby('contemporary_group')}
    
    def suggest_group_merges(self, df: pd.DataFrame, min_size: int = 5) -> List[Tuple[str, str]]:
        """Suggest merging small contemporary groups."""
        if 'contemporary_group' not in df.columns:
            return []
        
        group_counts = df['contemporary_group'].value_counts()
        small_groups = group_counts[group_counts < min_size]
        
        suggestions = []
        
        # Group small groups by management group
        small_group_info = df[df['contemporary_group'].isin(small_groups.index)][
            ['contemporary_group', 'mgmt_group']
        ].drop_duplicates()
        
        for mgmt_group in small_group_info['mgmt_group'].unique():
            mgmt_small_groups = small_group_info[
                small_group_info['mgmt_group'] == mgmt_group
            ]['contemporary_group'].tolist()
            
            if len(mgmt_small_groups) > 1:
                # Suggest merging all small groups in same management group
                suggestions.append((mgmt_small_groups[0], mgmt_small_groups[1]))
        
        return suggestions
