"""Streamlit app entry point for Streamlit Community Cloud deployment."""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import and run the main app
from webapp.app import main

if __name__ == "__main__":
    main()
