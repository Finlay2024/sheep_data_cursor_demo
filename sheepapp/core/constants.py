"""Constants and enums for sheep data analysis."""

from enum import Enum
from typing import Dict, Any

# Valid codes and ranges
SEX_CODES = {"Ewe", "Ram", "Wether"}

HEALTH_SCORES = {
    "footrot": {"min": 0, "max": 5, "description": "0=clean, 5=severe"},
    "dag": {"min": 0, "max": 5, "description": "0=clean, 5=severe"},
    "temperament": {"min": 1, "max": 5, "description": "1=poor, 5=excellent"}
}

# Trait categories for scoring
TRAIT_CATEGORIES = {
    "growth": ["adg_100_200d", "adg_200_300d", "wt_200d_adj", "wt_300d_adj"],
    "wool": ["gfw", "micron", "staple_len"],
    "reproduction": ["weaning_rate", "lambs_weaned"],
    "health": ["fec_count", "footrot_score", "dag_score"],
    "temperament": ["temperament"]
}

# Default configuration presets
DEFAULT_PRESETS = {
    "balanced": {
        "growth": 0.3,
        "wool": 0.2,
        "reproduction": 0.2,
        "health": 0.2,
        "temperament": 0.1
    },
    "meat": {
        "growth": 0.5,
        "wool": 0.1,
        "reproduction": 0.2,
        "health": 0.15,
        "temperament": 0.05
    },
    "wool": {
        "growth": 0.2,
        "wool": 0.4,
        "reproduction": 0.2,
        "health": 0.15,
        "temperament": 0.05
    },
    "worm": {
        "growth": 0.25,
        "wool": 0.15,
        "reproduction": 0.2,
        "health": 0.35,
        "temperament": 0.05
    }
}

class NormalizationMethod(str, Enum):
    PERCENTILE = "percentile"
    ZSCORE = "zscore"

class OutputFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    HTML = "html"
