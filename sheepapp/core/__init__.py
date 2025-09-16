"""Core data models and constants for sheep data analysis."""

from .models import SheepData, ContemporaryGroup, KPIs, ScoringResult
from .constants import SEX_CODES, HEALTH_SCORES

__all__ = [
    "SheepData",
    "ContemporaryGroup", 
    "KPIs",
    "ScoringResult",
    "SEX_CODES",
    "HEALTH_SCORES"
]
