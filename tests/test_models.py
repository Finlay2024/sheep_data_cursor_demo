"""Tests for data models and validation."""

import pytest
import pandas as pd
from datetime import date, datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sheepapp.core.models import SheepData, AnalysisConfig, ContemporaryGroup

class TestSheepData:
    """Test SheepData model validation."""
    
    def test_valid_sheep_data(self):
        """Test valid sheep data creation."""
        data = {
            'animal_id': 'A001',
            'sex': 'Ewe',
            'birth_date': date(2023, 8, 28),
            'mgmt_group': 'Mob1',
            'wt_birth': 4.9,
            'wt_200d': 67.0,
            'wt_300d': 59.0,
            'fec_count': 308,
            'footrot_score': 3,
            'dag_score': 5,
            'gfw': 4.54,
            'micron': 17.3,
            'staple_len': 89.7,
            'temperament': 5
        }
        
        sheep = SheepData(**data)
        assert sheep.animal_id == 'A001'
        assert sheep.sex == 'Ewe'
        assert sheep.wt_birth == 4.9
    
    def test_invalid_sex(self):
        """Test invalid sex validation."""
        data = {
            'animal_id': 'A001',
            'sex': 'Invalid',
            'birth_date': date(2023, 8, 28),
            'mgmt_group': 'Mob1'
        }
        
        with pytest.raises(ValueError, match="Invalid sex"):
            SheepData(**data)
    
    def test_future_birth_date(self):
        """Test future birth date validation."""
        data = {
            'animal_id': 'A001',
            'sex': 'Ewe',
            'birth_date': date(2030, 1, 1),
            'mgmt_group': 'Mob1'
        }
        
        with pytest.raises(ValueError, match="Birth date cannot be in the future"):
            SheepData(**data)
    
    def test_weight_progression_validation(self):
        """Test weight progression validation."""
        data = {
            'animal_id': 'A001',
            'sex': 'Ewe',
            'birth_date': date(2023, 8, 28),
            'mgmt_group': 'Mob1',
            'wt_birth': 5.0,
            'wt_100d': 3.0,  # Less than birth weight
            'wt_200d': 67.0
        }
        
        with pytest.raises(ValueError, match="100-day weight cannot be less than birth weight"):
            SheepData(**data)

class TestAnalysisConfig:
    """Test AnalysisConfig model."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = AnalysisConfig()
        assert config.min_birth_weight == 2.0
        assert config.max_footrot_score == 4
        assert config.weights['growth'] == 0.3
    
    def test_custom_config(self):
        """Test custom configuration creation."""
        config = AnalysisConfig(
            min_birth_weight=3.0,
            max_footrot_score=2,
            weights={'growth': 0.5, 'wool': 0.3, 'reproduction': 0.2}
        )
        assert config.min_birth_weight == 3.0
        assert config.max_footrot_score == 2
        assert config.weights['growth'] == 0.5
    
    def test_weights_validation(self):
        """Test weights sum validation."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            AnalysisConfig(weights={'growth': 0.5, 'wool': 0.3})  # Sums to 0.8

class TestContemporaryGroup:
    """Test ContemporaryGroup model."""
    
    def test_contemporary_group_creation(self):
        """Test contemporary group creation."""
        group = ContemporaryGroup(
            mgmt_group="Mob1",
            season_window="2023-Spring"
        )
        assert str(group) == "Mob1_2023-Spring"
    
    def test_contemporary_group_with_types(self):
        """Test contemporary group with birth and rearing types."""
        group = ContemporaryGroup(
            mgmt_group="Mob1",
            season_window="2023-Spring",
            birth_type="Twin",
            rearing_type="Dam"
        )
        assert str(group) == "Mob1_2023-Spring_Twin_Dam"
