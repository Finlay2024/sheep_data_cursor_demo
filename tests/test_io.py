"""Tests for IO modules."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sheepapp.io import DataLoader, load_demo_data
from sheepapp.io.validators import SchemaValidator

class TestDataLoader:
    """Test DataLoader functionality."""
    
    def test_load_csv(self):
        """Test CSV loading."""
        # Create temporary CSV file
        data = {
            'animal_id': ['A001', 'A002'],
            'sex': ['Ewe', 'Ram'],
            'birth_date': ['2023-08-28', '2023-09-10'],
            'mgmt_group': ['Mob1', 'Mob1'],
            'wt_birth': [4.9, 3.3]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            loader = DataLoader()
            loaded_df = loader.load_csv(temp_path)
            
            assert len(loaded_df) == 2
            assert 'animal_id' in loaded_df.columns
            assert 'sex' in loaded_df.columns
            
        finally:
            Path(temp_path).unlink()
    
    def test_validate_and_clean(self):
        """Test data validation and cleaning."""
        data = {
            'animal_id': ['A001', 'A002'],
            'sex': ['Ewe', 'Ram'],
            'birth_date': ['2023-08-28', '2023-09-10'],
            'mgmt_group': ['Mob1', 'Mob1'],
            'wt_birth': [4.9, 3.3]
        }
        df = pd.DataFrame(data)
        
        loader = DataLoader()
        cleaned_df = loader.validate_and_clean(df, "test.csv")
        
        assert 'source_file' in cleaned_df.columns
        assert 'import_timestamp' in cleaned_df.columns
        assert 'row_hash' in cleaned_df.columns
        assert cleaned_df['source_file'].iloc[0] == "test.csv"

class TestSchemaValidator:
    """Test SchemaValidator functionality."""
    
    def test_validate_schema_valid(self):
        """Test validation of valid schema."""
        data = {
            'animal_id': ['A001', 'A002'],
            'sex': ['Ewe', 'Ram'],
            'birth_date': ['2023-08-28', '2023-09-10'],
            'mgmt_group': ['Mob1', 'Mob1']
        }
        df = pd.DataFrame(data)
        
        validator = SchemaValidator()
        results = validator.validate_schema(df)
        
        assert results['valid'] == True
        assert len(results['issues']) == 0
    
    def test_validate_schema_missing_required(self):
        """Test validation with missing required fields."""
        data = {
            'animal_id': ['A001', 'A002'],
            'sex': ['Ewe', 'Ram']
            # Missing birth_date and mgmt_group
        }
        df = pd.DataFrame(data)
        
        validator = SchemaValidator()
        results = validator.validate_schema(df)
        
        assert results['valid'] == False
        assert len(results['issues']) > 0
        assert any('Missing required fields' in issue for issue in results['issues'])
    
    def test_validate_schema_invalid_sex(self):
        """Test validation with invalid sex values."""
        data = {
            'animal_id': ['A001', 'A002'],
            'sex': ['Ewe', 'Invalid'],
            'birth_date': ['2023-08-28', '2023-09-10'],
            'mgmt_group': ['Mob1', 'Mob1']
        }
        df = pd.DataFrame(data)
        
        validator = SchemaValidator()
        results = validator.validate_schema(df)
        
        assert results['valid'] == False
        assert any('Invalid sex values' in issue for issue in results['issues'])
    
    def test_get_data_quality_report(self):
        """Test data quality report generation."""
        data = {
            'animal_id': ['A001', 'A002', 'A003'],
            'sex': ['Ewe', 'Ram', 'Ewe'],
            'birth_date': ['2023-08-28', '2023-09-10', None],
            'mgmt_group': ['Mob1', 'Mob1', 'Mob2'],
            'wt_birth': [4.9, 3.3, None]
        }
        df = pd.DataFrame(data)
        
        validator = SchemaValidator()
        report = validator.get_data_quality_report(df)
        
        assert report['total_rows'] == 3
        assert report['total_columns'] == 5
        assert 'missing_data' in report
        assert 'data_types' in report

class TestLoadDemoData:
    """Test demo data loading."""
    
    def test_load_demo_data_exists(self):
        """Test that demo data can be loaded."""
        try:
            df = load_demo_data()
            assert len(df) > 0
            assert 'animal_id' in df.columns
            assert 'sex' in df.columns
        except FileNotFoundError:
            pytest.skip("Demo data file not found")
