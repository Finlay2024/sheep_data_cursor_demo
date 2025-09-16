# 🐑 Sheep Data Analysis Application

A comprehensive Python framework for analyzing sheep data, ranking rams for selection, and recommending flock reductions with configurable trait weights and filters.

## Features

- **Data Processing**: Load and validate CSV/Excel/Parquet files with comprehensive schema validation
- **KPI Calculation**: Compute key performance indicators including ADG, age-adjusted weights, FEC, wool metrics, reproduction rates, and BSE status
- **Contemporary Grouping**: Group animals by management and birth date windows for fair comparison
- **Scoring & Ranking**: Configurable weighted scoring system with hard and soft filters
- **Selection Recommendations**: Rank rams for breeding selection with detailed explanations
- **Cull Recommendations**: Identify animals for culling with explicit reasons
- **Multiple Export Formats**: Generate CSV, Excel, and HTML reports with charts
- **Web Interface**: User-friendly Streamlit application with multi-page workflow
- **Configuration Presets**: Pre-configured settings for different selection strategies

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sheep-data-demo-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Using the Web Application

Launch the Streamlit web interface:
```bash
python cli.py web
```

Or run directly:
```bash
streamlit run webapp/app.py
```

The application will open in your browser at `http://localhost:8501`.

### Using the Command Line Interface

Run complete analysis with demo data:
```bash
python cli.py analyze --demo
```

Run analysis with your own data:
```bash
python cli.py analyze --input your_data.csv --preset balanced
```

Validate data file:
```bash
python cli.py validate --input your_data.csv
```

List available presets:
```bash
python cli.py presets
```

## Data Format

The application expects data with the following columns:

### Required Fields
- `animal_id`: Unique animal identifier
- `sex`: Animal sex (Ewe, Ram, Wether)
- `birth_date`: Birth date (YYYY-MM-DD format)
- `mgmt_group`: Management group identifier

### Optional Fields
- `sire_id`, `dam_id`: Parent identifiers
- `wt_birth`, `wt_100d`, `wt_wean`, `wt_200d`, `wt_300d`: Weight measurements (kg)
- `preg_scan`: Pregnancy scan result (0-1)
- `lambs_born`, `lambs_weaned`: Reproduction data
- `fec_count`: Faecal egg count
- `footrot_score`, `dag_score`: Health scores (0-5)
- `gfw`, `micron`, `staple_len`: Wool measurements
- `temperament`: Temperament score (1-5)
- `cull_flag`, `cull_reason`: Existing cull information

## Configuration Presets

The application includes four pre-configured selection strategies:

### Balanced (Default)
- Equal emphasis on all trait categories
- Suitable for general-purpose breeding programs

### Meat
- Focus on growth and meat production traits
- Higher weights for growth metrics

### Wool
- Focus on wool production and quality
- Emphasis on fleece weight and fiber characteristics

### Worm
- Focus on health and worm resistance
- Higher weights for health metrics and FEC

## Web Application Workflow

1. **📤 Data Upload**: Upload your data file or use the demo dataset
2. **🔍 Data Quality**: Review data quality, missing values, and outliers
3. **📈 KPIs**: Calculate and visualize key performance indicators
4. **🧮 Selection Weights**: Configure trait weights and filter settings
5. **🏅 Ram Results**: View ranked rams with detailed scoring
6. **✂️ Cull Recommendations**: Review animals recommended for culling
7. **🧾 Reports & Export**: Generate and download comprehensive reports

## Architecture

```
sheepapp/
├── core/           # Data models and constants
├── io/             # Data loading and validation
├── processing/     # Data cleaning and grouping
├── metrics/        # KPI calculations
├── scoring/        # Filtering and ranking
├── reports/        # Export functionality
└── config_presets/ # Configuration presets

webapp/             # Streamlit web interface
tests/              # Test suite
```

## Key Metrics Calculated

### Growth Metrics
- Average Daily Gain (ADG) between measurement periods
- Age-adjusted weights for fair comparison
- Growth rate consistency

### Wool Metrics
- Clean Fleece Weight (CFW) estimation
- Fiber diameter (micron) scoring
- Staple length assessment

### Reproduction Metrics
- Weaning rate (lambs weaned / lambs born)
- Pregnancy success rate
- Reproductive efficiency

### Health Metrics
- Faecal Egg Count (FEC) scoring
- Composite health score from footrot and DAG
- BSE (Breeding Soundness Examination) pass/fail

## Filtering System

### Hard Filters (Eliminate animals)
- Minimum birth weight
- Maximum footrot/DAG scores
- Minimum weaning weight
- Maximum micron
- BSE pass requirement

### Soft Filters (Flag animals)
- Low 200d/300d weights
- Poor weaning rates
- Other performance indicators

## Scoring System

1. **Trait Standardization**: Normalize traits within contemporary groups
2. **Category Scoring**: Calculate scores for growth, wool, reproduction, health, temperament
3. **Weighted Combination**: Combine category scores using configurable weights
4. **Ranking**: Rank animals by composite score

## Export Formats

### CSV Files
- Ranked rams with scores and rankings
- Cull recommendations with reasons
- Detailed KPI data

### Excel Files
- Multi-sheet workbooks with summary statistics
- Formatted tables with charts

### HTML Reports
- Comprehensive analysis reports
- Interactive charts and visualizations
- Configuration metadata

## Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/test_models.py
pytest tests/test_io.py
pytest tests/test_metrics.py
```

## Requirements

- Python 3.11+
- pandas >= 2.0.0
- pydantic >= 2.0.0
- streamlit >= 1.28.0
- plotly >= 5.15.0
- xlsxwriter >= 3.1.0
- openpyxl >= 3.1.0

## Demo Data

The application includes `Synthetic_Sheep_Data.csv` with 100 synthetic sheep records for testing and demonstration purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on the GitHub repository or contact the development team.
