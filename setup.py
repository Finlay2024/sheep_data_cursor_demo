#!/usr/bin/env python3
"""Setup script for sheep data analysis application."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="sheep-data-analysis",
    version="1.0.0",
    author="Sheep Data Analysis Team",
    description="A comprehensive Python framework for analyzing sheep data, ranking rams for selection, and recommending flock reductions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sheep-analyze=cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="sheep, livestock, breeding, selection, data analysis, agriculture",
    project_urls={
        "Bug Reports": "https://github.com/your-org/sheep-data-analysis/issues",
        "Source": "https://github.com/your-org/sheep-data-analysis",
        "Documentation": "https://github.com/your-org/sheep-data-analysis#readme",
    },
)
