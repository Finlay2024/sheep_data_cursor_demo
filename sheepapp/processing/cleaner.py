"""Data cleaning and preprocessing."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans and preprocesses sheep data."""
    
    def __init__(self):
        self.cleaning_log = []
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main cleaning pipeline."""
        logger.info(f"Starting data cleaning for {len(df)} rows")
        
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Step 1: Handle missing values
        cleaned_df = self._handle_missing_values(cleaned_df)
        
        # Step 2: Fix data types
        cleaned_df = self._fix_data_types(cleaned_df)
        
        # Step 3: Standardize text fields
        cleaned_df = self._standardize_text(cleaned_df)
        
        # Step 4: Validate ranges
        cleaned_df = self._validate_ranges(cleaned_df)
        
        # Step 5: Handle outliers
        cleaned_df = self._handle_outliers(cleaned_df)
        
        # Step 6: Calculate derived fields
        cleaned_df = self._calculate_derived_fields(cleaned_df)
        
        logger.info(f"Data cleaning completed. {len(self.cleaning_log)} issues addressed")
        return cleaned_df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately."""
        # For numeric columns, we'll keep NaN for now (will be handled in metrics calculation)
        # For categorical columns, we can fill with 'Unknown' or similar
        
        categorical_cols = ['sire_id', 'dam_id', 'cull_reason']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
        
        # Fill cull_flag with 0 if missing
        if 'cull_flag' in df.columns:
            df['cull_flag'] = df['cull_flag'].fillna(0)
        
        return df
    
    def _fix_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure correct data types."""
        # Convert date columns
        if 'birth_date' in df.columns:
            df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = [
            'wt_birth', 'wt_100d', 'wt_wean', 'wt_200d', 'wt_300d',
            'preg_scan', 'lambs_born', 'lambs_weaned', 'fec_count',
            'gfw', 'micron', 'staple_len'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert integer columns
        int_cols = ['footrot_score', 'dag_score', 'temperament', 'cull_flag']
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        return df
    
    def _standardize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize text fields."""
        # Standardize sex field
        if 'sex' in df.columns:
            df['sex'] = df['sex'].str.strip().str.title()
            # Map common variations
            sex_mapping = {
                'Female': 'Ewe',
                'Male': 'Ram',
                'Castrated': 'Wether'
            }
            df['sex'] = df['sex'].replace(sex_mapping)
        
        # Standardize management group
        if 'mgmt_group' in df.columns:
            df['mgmt_group'] = df['mgmt_group'].str.strip().str.upper()
        
        return df
    
    def _validate_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and fix values outside expected ranges."""
        # Health scores (0-5)
        health_cols = ['footrot_score', 'dag_score']
        for col in health_cols:
            if col in df.columns:
                # Cap at 5, floor at 0
                df[col] = df[col].clip(0, 5)
        
        # Temperament (1-5)
        if 'temperament' in df.columns:
            df['temperament'] = df['temperament'].clip(1, 5)
        
        # Pregnancy scan (0-1)
        if 'preg_scan' in df.columns:
            df['preg_scan'] = df['preg_scan'].clip(0, 1)
        
        # Weights should be positive
        weight_cols = ['wt_birth', 'wt_100d', 'wt_wean', 'wt_200d', 'wt_300d', 'gfw']
        for col in weight_cols:
            if col in df.columns:
                # Set negative weights to NaN
                df.loc[df[col] < 0, col] = np.nan
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle statistical outliers using IQR method."""
        numeric_cols = [
            'wt_birth', 'wt_100d', 'wt_wean', 'wt_200d', 'wt_300d',
            'fec_count', 'gfw', 'micron', 'staple_len'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier bounds
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Count outliers
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                if outliers > 0:
                    self.cleaning_log.append(f"Found {outliers} outliers in {col}")
                    # Cap outliers instead of removing
                    df[col] = df[col].clip(lower_bound, upper_bound)
        
        return df
    
    def _calculate_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived fields that will be useful for analysis."""
        # Calculate age in days
        if 'birth_date' in df.columns:
            today = pd.Timestamp.now().normalize()
            df['age_days'] = (today - df['birth_date']).dt.days
        
        # Calculate weaning rate
        if 'lambs_born' in df.columns and 'lambs_weaned' in df.columns:
            df['weaning_rate'] = df['lambs_weaned'] / df['lambs_born']
            # Handle division by zero
            df['weaning_rate'] = df['weaning_rate'].replace([np.inf, -np.inf], np.nan)
        
        # Calculate clean fleece weight (CFW) from greasy fleece weight (GFW)
        # Typical yield is around 60-70% for most sheep breeds
        if 'gfw' in df.columns:
            df['cfw'] = df['gfw'] * 0.65  # Assume 65% yield
        
        return df
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Get summary of cleaning operations performed."""
        return {
            'total_issues': len(self.cleaning_log),
            'issues': self.cleaning_log,
            'timestamp': datetime.now().isoformat()
        }
    
    def identify_data_quality_issues(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Identify potential data quality issues."""
        issues = {
            'missing_data': [],
            'outliers': [],
            'inconsistencies': [],
            'warnings': []
        }
        
        # Check for missing critical data
        critical_cols = ['animal_id', 'sex', 'birth_date', 'mgmt_group']
        for col in critical_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    issues['missing_data'].append(f"{col}: {missing_count} missing values")
        
        # Check for weight inconsistencies
        if all(col in df.columns for col in ['wt_birth', 'wt_100d', 'wt_200d']):
            inconsistent = df[
                (df['wt_100d'] < df['wt_birth']) | 
                (df['wt_200d'] < df['wt_100d'])
            ]
            if not inconsistent.empty:
                issues['inconsistencies'].append(
                    f"Weight progression issues: {len(inconsistent)} animals"
                )
        
        # Check for extreme values
        if 'fec_count' in df.columns:
            extreme_fec = df[df['fec_count'] > 1000]
            if not extreme_fec.empty:
                issues['outliers'].append(f"Extreme FEC values: {len(extreme_fec)} animals")
        
        return issues
