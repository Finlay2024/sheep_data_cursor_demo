"""Pydantic models for sheep data validation and processing."""

from datetime import datetime, date
from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd

class SheepData(BaseModel):
    """Core sheep data model with validation."""
    
    animal_id: str = Field(..., description="Unique animal identifier")
    sex: str = Field(..., description="Sex: Ewe, Ram, or Wether")
    birth_date: date = Field(..., description="Birth date")
    sire_id: Optional[str] = Field(None, description="Sire identifier")
    dam_id: Optional[str] = Field(None, description="Dam identifier")
    mgmt_group: str = Field(..., description="Management group")
    
    # Weight measurements
    wt_birth: Optional[float] = Field(None, ge=0, description="Birth weight (kg)")
    wt_100d: Optional[float] = Field(None, ge=0, description="100-day weight (kg)")
    wt_wean: Optional[float] = Field(None, ge=0, description="Weaning weight (kg)")
    wt_200d: Optional[float] = Field(None, ge=0, description="200-day weight (kg)")
    wt_300d: Optional[float] = Field(None, ge=0, description="300-day weight (kg)")
    
    # Reproduction data
    preg_scan: Optional[float] = Field(None, ge=0, le=1, description="Pregnancy scan result")
    lambs_born: Optional[float] = Field(None, ge=0, description="Number of lambs born")
    lambs_weaned: Optional[float] = Field(None, ge=0, description="Number of lambs weaned")
    
    # Health measurements
    fec_count: Optional[float] = Field(None, ge=0, description="Faecal egg count")
    footrot_score: Optional[int] = Field(None, ge=0, le=5, description="Footrot score (0-5)")
    dag_score: Optional[int] = Field(None, ge=0, le=5, description="DAG score (0-5)")
    
    # Wool measurements
    gfw: Optional[float] = Field(None, ge=0, description="Greasy fleece weight (kg)")
    micron: Optional[float] = Field(None, ge=0, description="Fibre diameter (microns)")
    staple_len: Optional[float] = Field(None, ge=0, description="Staple length (mm)")
    
    # Other traits
    temperament: Optional[int] = Field(None, ge=1, le=5, description="Temperament score (1-5)")
    
    # Culling information
    cull_flag: Optional[int] = Field(0, ge=0, le=1, description="Cull flag (0=keep, 1=cull)")
    cull_reason: Optional[str] = Field(None, description="Reason for culling")
    
    # Metadata
    source_file: Optional[str] = Field(None, description="Source file name")
    import_timestamp: Optional[datetime] = Field(None, description="Import timestamp")
    row_hash: Optional[str] = Field(None, description="Row content hash")
    
    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v):
        if v not in {"Ewe", "Ram", "Wether"}:
            raise ValueError(f"Invalid sex: {v}. Must be one of: Ewe, Ram, Wether")
        return v
    
    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v):
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v
    
    @model_validator(mode='after')
    def validate_measurement_dates(self):
        """Validate that measurement dates are after birth date."""
        if not self.birth_date:
            return self
            
        # Check that weights are reasonable for age
        if self.wt_100d and self.wt_100d < (self.wt_birth or 0):
            raise ValueError("100-day weight cannot be less than birth weight")
        if self.wt_200d and self.wt_100d and self.wt_200d < self.wt_100d:
            raise ValueError("200-day weight cannot be less than 100-day weight")
        if self.wt_300d and self.wt_200d and self.wt_300d < self.wt_200d:
            raise ValueError("300-day weight cannot be less than 200-day weight")
            
        return self

class ContemporaryGroup(BaseModel):
    """Contemporary group definition."""
    
    mgmt_group: str
    season_window: str  # e.g., "2023-Spring"
    birth_type: Optional[str] = None  # e.g., "Single", "Twin"
    rearing_type: Optional[str] = None  # e.g., "Dam", "Foster"
    
    def __str__(self):
        parts = [self.mgmt_group, self.season_window]
        if self.birth_type:
            parts.append(self.birth_type)
        if self.rearing_type:
            parts.append(self.rearing_type)
        return "_".join(parts)

class KPIs(BaseModel):
    """Key Performance Indicators for an animal."""
    
    animal_id: str
    
    # Growth metrics
    adg_100_200d: Optional[float] = None  # Average daily gain 100-200d
    adg_200_300d: Optional[float] = None  # Average daily gain 200-300d
    wt_200d_adj: Optional[float] = None   # Age-adjusted 200d weight
    wt_300d_adj: Optional[float] = None   # Age-adjusted 300d weight
    
    # Wool metrics
    cfw: Optional[float] = None  # Clean fleece weight (estimated from GFW)
    micron_adj: Optional[float] = None  # Adjusted micron
    staple_len_adj: Optional[float] = None  # Adjusted staple length
    
    # Reproduction metrics
    weaning_rate: Optional[float] = None  # Lambs weaned / lambs born
    
    # Health metrics
    fec_adj: Optional[float] = None  # Adjusted FEC
    health_score: Optional[float] = None  # Composite health score
    
    # Overall metrics
    bse_pass: Optional[bool] = None  # BSE pass/fail
    contemporary_group: Optional[str] = None

class ScoringResult(BaseModel):
    """Scoring result for an animal."""
    
    animal_id: str
    final_score: float
    rank: int
    
    # Filter results
    hard_filters_passed: bool
    hard_filters_hit: List[str] = []
    soft_filters_passed: bool
    soft_filters_hit: List[str] = []
    
    # Component scores
    component_scores: Dict[str, float] = {}
    trait_scores: Dict[str, float] = {}
    
    # Explainability
    explanation: Dict[str, Any] = {}
    
    # Culling recommendation
    cull_recommended: bool = False
    cull_reason: Optional[str] = None

class AnalysisConfig(BaseModel):
    """Configuration for analysis parameters."""
    
    # Data settings
    contemporary_group_window_days: int = 30
    normalization_method: str = "percentile"
    
    # Filter thresholds
    min_birth_weight: float = 2.0
    max_footrot_score: int = 4
    max_dag_score: int = 4
    min_weaning_weight: float = 20.0
    max_micron: float = 25.0
    bse_pass_required: bool = True
    
    # Scoring weights
    weights: Dict[str, float] = {
        "growth": 0.3,
        "wool": 0.2,
        "reproduction": 0.2,
        "health": 0.2,
        "temperament": 0.1
    }
    
    # Trait weights within categories
    trait_weights: Dict[str, Dict[str, float]] = {
        "growth": {
            "adg_100_200d": 0.3,
            "adg_200_300d": 0.3,
            "wt_200d_adj": 0.2,
            "wt_300d_adj": 0.2
        },
        "wool": {
            "gfw": 0.4,
            "micron": 0.3,
            "staple_len": 0.3
        },
        "reproduction": {
            "weaning_rate": 0.6,
            "lambs_weaned": 0.4
        },
        "health": {
            "fec_count": 0.4,
            "footrot_score": 0.3,
            "dag_score": 0.3
        },
        "temperament": {
            "temperament": 1.0
        }
    }
    
    @field_validator('weights')
    @classmethod
    def validate_weights_sum(cls, v):
        if abs(sum(v.values()) - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")
        return v
