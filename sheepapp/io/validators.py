"""Data validation and schema checking."""

import pandas as pd
from typing import Dict, List, Any, Tuple
import logging

from ..core.constants import SEX_CODES, HEALTH_SCORES

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates sheep data schema and content."""
    
    def __init__(self):
        self.required_fields = [
            'animal_id', 'sex', 'birth_date', 'mgmt_group'
        ]
        
        self.optional_fields = [
            'sire_id', 'dam_id', 'wt_birth', 'wt_100d', 'wt_wean', 
            'wt_200d', 'wt_300d', 'preg_scan', 'lambs_born', 'lambs_weaned',
            'fec_count', 'footrot_score', 'dag_score', 'gfw', 'micron',
            'staple_len', 'temperament', 'cull_flag', 'cull_reason'
        ]
    
    def validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the schema of the dataframe."""
        issues = []
        warnings = []
        
        # Check required fields
        missing_required = set(self.required_fields) - set(df.columns)
        if missing_required:
            issues.append(f"Missing required fields: {missing_required}")
        
        # Check for unexpected fields
        all_expected = set(self.required_fields + self.optional_fields)
        unexpected = set(df.columns) - all_expected
        if unexpected:
            warnings.append(f"Unexpected fields: {unexpected}")
        
        # Check data types and ranges
        type_issues = self._validate_data_types(df)
        issues.extend(type_issues)
        
        # Check value ranges
        range_issues = self._validate_value_ranges(df)
        issues.extend(range_issues)
        
        # Check for duplicates
        duplicate_issues = self._check_duplicates(df)
        issues.extend(duplicate_issues)
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'summary': {
                'total_rows': len(df),
                'missing_required': len(missing_required),
                'unexpected_fields': len(unexpected),
                'type_issues': len(type_issues),
                'range_issues': len(range_issues),
                'duplicate_issues': len(duplicate_issues)
            }
        }
    
    def _validate_data_types(self, df: pd.DataFrame) -> List[str]:
        """Validate data types of columns."""
        issues = []
        
        # Check animal_id is string and unique
        if 'animal_id' in df.columns:
            if not df['animal_id'].dtype == 'object':
                issues.append("animal_id should be string type")
        
        # Check sex values
        if 'sex' in df.columns:
            invalid_sex = df[~df['sex'].isin(SEX_CODES)]
            if not invalid_sex.empty:
                issues.append(f"Invalid sex values: {invalid_sex['sex'].unique().tolist()}")
        
        # Check date format
        if 'birth_date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['birth_date']):
                issues.append("birth_date should be datetime type")
        
        return issues
    
    def _validate_value_ranges(self, df: pd.DataFrame) -> List[str]:
        """Validate value ranges for numeric columns."""
        issues = []
        
        # Check health scores
        for score_col, limits in HEALTH_SCORES.items():
            if score_col in df.columns:
                col_data = df[score_col].dropna()
                if not col_data.empty:
                    if (col_data < limits['min']).any() or (col_data > limits['max']).any():
                        issues.append(f"{score_col} values outside range {limits['min']}-{limits['max']}")
        
        # Check pregnancy scan
        if 'preg_scan' in df.columns:
            col_data = df['preg_scan'].dropna()
            if not col_data.empty:
                if (col_data < 0).any() or (col_data > 1).any():
                    issues.append("preg_scan values should be 0-1")
        
        # Check weights are positive
        weight_cols = ['wt_birth', 'wt_100d', 'wt_wean', 'wt_200d', 'wt_300d', 'gfw']
        for col in weight_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if not col_data.empty and (col_data < 0).any():
                    issues.append(f"{col} should be positive")
        
        return issues
    
    def _check_duplicates(self, df: pd.DataFrame) -> List[str]:
        """Check for duplicate animal IDs."""
        issues = []
        
        if 'animal_id' in df.columns:
            duplicates = df[df['animal_id'].duplicated()]
            if not duplicates.empty:
                issues.append(f"Duplicate animal_id values: {duplicates['animal_id'].tolist()}")
        
        return issues
    
    def get_data_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive data quality report."""
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_data': {},
            'outliers': {},
            'data_types': {},
            'value_counts': {}
        }
        
        # Missing data analysis
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            report['missing_data'][col] = {
                'count': int(missing_count),
                'percentage': round(missing_pct, 2)
            }
        
        # Data types
        for col in df.columns:
            report['data_types'][col] = str(df[col].dtype)
        
        # Value counts for categorical columns
        categorical_cols = ['sex', 'mgmt_group', 'cull_reason']
        for col in categorical_cols:
            if col in df.columns:
                report['value_counts'][col] = df[col].value_counts().to_dict()
        
        return report
