"""Command-line interface for sheep data analysis."""

import typer
from pathlib import Path
import sys
import logging

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from sheepapp.io import DataLoader, load_demo_data
from sheepapp.processing import DataCleaner, ContemporaryGrouping, DataStandardizer
from sheepapp.metrics import MetricsCalculator
from sheepapp.scoring import ScoringEngine
from sheepapp.config_presets import ConfigPresets
from sheepapp.core.models import AnalysisConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer(help="Sheep Data Analysis CLI")

@app.command()
def analyze(
    input_file: str = typer.Option(None, "--input", "-i", help="Input data file (CSV/Excel/Parquet)"),
    output_dir: str = typer.Option("output", "--output", "-o", help="Output directory"),
    preset: str = typer.Option("balanced", "--preset", "-p", help="Configuration preset"),
    demo: bool = typer.Option(False, "--demo", "-d", help="Use demo dataset")
):
    """Run complete sheep data analysis."""
    
    try:
        # Load data
        if demo:
            logger.info("Using demo dataset")
            df = load_demo_data()
        elif input_file:
            logger.info(f"Loading data from {input_file}")
            loader = DataLoader()
            df = loader.load_file(input_file)
            df = loader.validate_and_clean(df, input_file)
        else:
            raise typer.BadParameter("Either --demo flag or --input file must be provided")
        
        logger.info(f"Loaded {len(df)} animals")
        
        # Load configuration
        presets = ConfigPresets()
        config = presets.create_config_from_preset(preset)
        logger.info(f"Using preset: {preset}")
        
        # Run analysis
        scoring_engine = ScoringEngine(config)
        results = scoring_engine.score_animals(df)
        
        # Export results
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = scoring_engine.export_results(str(output_path))
        
        logger.info("Analysis completed successfully!")
        logger.info(f"Results exported to: {output_path}")
        
        for file_type, file_path in exported_files.items():
            logger.info(f"  {file_type}: {file_path}")
        
        # Print summary
        summary = scoring_engine.get_summary_statistics()
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total animals processed: {summary['total_animals_processed']}")
        print(f"Animals after hard filters: {summary['animals_after_hard_filters']}")
        print(f"Total rams ranked: {summary['total_rams_ranked']}")
        print(f"Cull recommendations: {summary['cull_recommendations']}")
        print(f"Retention rate: {summary['retention_rate']:.1f}%")
        
        if summary['total_rams_ranked'] > 0:
            print("\nTop 5 Rams:")
            top_rams = scoring_engine.get_top_rams(5)
            for _, ram in top_rams.iterrows():
                print(f"  {ram['rank']}. {ram['animal_id']} - Score: {ram['composite_score']:.3f}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise typer.Exit(1)

@app.command()
def validate(
    input_file: str = typer.Option(..., "--input", "-i", help="Input data file to validate")
):
    """Validate data file schema and quality."""
    
    try:
        logger.info(f"Validating data file: {input_file}")
        
        loader = DataLoader()
        df = loader.load_file(input_file)
        validation_results = loader.validator.validate_schema(df)
        
        print("\n" + "="*50)
        print("DATA VALIDATION RESULTS")
        print("="*50)
        
        if validation_results['valid']:
            print("✅ Data validation PASSED")
        else:
            print("❌ Data validation FAILED")
            print("\nIssues found:")
            for issue in validation_results['issues']:
                print(f"  - {issue}")
        
        if validation_results['warnings']:
            print("\nWarnings:")
            for warning in validation_results['warnings']:
                print(f"  - {warning}")
        
        print(f"\nSummary:")
        print(f"  Total rows: {validation_results['summary']['total_rows']}")
        print(f"  Missing required fields: {validation_results['summary']['missing_required']}")
        print(f"  Unexpected fields: {validation_results['summary']['unexpected_fields']}")
        print(f"  Type issues: {validation_results['summary']['type_issues']}")
        print(f"  Range issues: {validation_results['summary']['range_issues']}")
        print(f"  Duplicate issues: {validation_results['summary']['duplicate_issues']}")
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)

@app.command()
def presets():
    """List available configuration presets."""
    
    try:
        presets = ConfigPresets()
        available_presets = presets.get_available_presets()
        
        print("\n" + "="*50)
        print("AVAILABLE PRESETS")
        print("="*50)
        
        for preset in available_presets:
            preset_data = presets.get_preset(preset)
            description = preset_data.get('description', 'No description available')
            print(f"\n{preset.upper()}:")
            print(f"  Description: {description}")
            
            if 'weights' in preset_data:
                print("  Category weights:")
                for category, weight in preset_data['weights'].items():
                    print(f"    {category}: {weight}")
        
    except Exception as e:
        logger.error(f"Failed to list presets: {str(e)}")
        raise typer.Exit(1)

@app.command()
def web():
    """Launch the Streamlit web application."""
    
    import subprocess
    import os
    
    try:
        # Get the path to the Streamlit app
        app_path = Path(__file__).parent / "webapp" / "app.py"
        
        logger.info("Launching Streamlit web application...")
        logger.info("The application will open in your default web browser")
        logger.info("Press Ctrl+C to stop the application")
        
        # Run Streamlit
        subprocess.run([
            "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to launch web application: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
