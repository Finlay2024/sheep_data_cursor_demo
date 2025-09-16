"""Data loaders for various file formats."""

import pandas as pd
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import logging

from ..core.models import SheepData
from .validators import SchemaValidator

logger = logging.getLogger(__name__)

class DataLoader:
    """Loads sheep data from various file formats."""
    
    def __init__(self):
        self.validator = SchemaValidator()
    
    def load_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load data from CSV file."""
        try:
            df = pd.read_csv(file_path, **kwargs)
            logger.info(f"Loaded CSV with {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV from {file_path}: {e}")
            raise
    
    def load_excel(self, file_path: Union[str, Path], sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """Load data from Excel file."""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            logger.info(f"Loaded Excel with {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading Excel from {file_path}: {e}")
            raise
    
    def load_parquet(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load data from Parquet file."""
        try:
            df = pd.read_parquet(file_path, **kwargs)
            logger.info(f"Loaded Parquet with {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading Parquet from {file_path}: {e}")
            raise
    
    def load_file(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load data from file based on extension."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            return self.load_csv(file_path, **kwargs)
        elif suffix in ['.xlsx', '.xls']:
            return self.load_excel(file_path, **kwargs)
        elif suffix == '.parquet':
            return self.load_parquet(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def validate_and_clean(self, df: pd.DataFrame, source_file: Optional[str] = None) -> pd.DataFrame:
        """Validate and clean the loaded data."""
        # Add metadata
        if source_file:
            df['source_file'] = source_file
        df['import_timestamp'] = datetime.now()
        
        # Generate row hashes for tracking
        df['row_hash'] = df.apply(
            lambda row: hashlib.md5(str(row.values).encode()).hexdigest()[:16],
            axis=1
        )
        
        # Validate schema
        validation_results = self.validator.validate_schema(df)
        if not validation_results['valid']:
            logger.warning(f"Schema validation issues: {validation_results['issues']}")
        
        # Clean data
        df = self._clean_data(df)
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the data by standardizing formats and handling missing values."""
        # Convert date columns
        if 'birth_date' in df.columns:
            df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce').dt.date
        
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
        
        # Standardize text columns
        if 'sex' in df.columns:
            df['sex'] = df['sex'].str.strip().str.title()
        
        # Fill missing cull_flag with 0
        if 'cull_flag' in df.columns:
            df['cull_flag'] = df['cull_flag'].fillna(0)
        
        return df
    
    def load_and_validate(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load file and validate the data."""
        df = self.load_file(file_path, **kwargs)
        return self.validate_and_clean(df, str(file_path))

def load_demo_data() -> pd.DataFrame:
    """Load the demo synthetic sheep data."""
    demo_path = Path(__file__).parent.parent.parent / "Synthetic_Sheep_Data.csv"
    
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo data file not found: {demo_path}")
    
    loader = DataLoader()
    return loader.load_and_validate(demo_path)
