"""Report writers for various output formats."""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

try:
    import xlsxwriter
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

logger = logging.getLogger(__name__)

class ReportWriter:
    """Writes analysis results to various formats."""
    
    def __init__(self, output_dir: Union[str, Path] = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def write_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Write DataFrame to CSV file."""
        filepath = self.output_dir / f"{filename}.csv"
        df.to_csv(filepath, index=False)
        logger.info(f"Written CSV report: {filepath}")
        return filepath
    
    def write_excel(self, data: Dict[str, pd.DataFrame], filename: str) -> Path:
        """Write multiple DataFrames to Excel file with multiple sheets."""
        if not XLSX_AVAILABLE:
            raise ImportError("xlsxwriter is required for Excel output")
        
        filepath = self.output_dir / f"{filename}.xlsx"
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            for sheet_name, df in data.items():
                # Truncate sheet name to Excel limit
                sheet_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Written Excel report: {filepath}")
        return filepath
    
    def write_html(self, content: str, filename: str) -> Path:
        """Write HTML content to file."""
        filepath = self.output_dir / f"{filename}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Written HTML report: {filepath}")
        return filepath
    
    def write_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Write data to JSON file."""
        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Written JSON report: {filepath}")
        return filepath
    
    def write_ranked_rams(self, results: List[Dict[str, Any]], filename: str = "ranked_rams") -> Path:
        """Write ranked ram results to CSV and Excel."""
        df = pd.DataFrame(results)
        
        # Write CSV
        csv_path = self.write_csv(df, filename)
        
        # Write Excel if available
        if XLSX_AVAILABLE:
            excel_data = {
                "Ranked Rams": df,
                "Summary": self._create_summary_sheet(df)
            }
            excel_path = self.write_excel(excel_data, filename)
            return excel_path
        
        return csv_path
    
    def write_cull_recommendations(self, recommendations: List[Dict[str, Any]], filename: str = "cull_recommendations") -> Path:
        """Write cull recommendations to CSV and Excel."""
        df = pd.DataFrame(recommendations)
        
        # Write CSV
        csv_path = self.write_csv(df, filename)
        
        # Write Excel if available
        if XLSX_AVAILABLE:
            excel_data = {
                "Cull Recommendations": df,
                "Summary": self._create_cull_summary_sheet(df)
            }
            excel_path = self.write_excel(excel_data, filename)
            return excel_path
        
        return csv_path
    
    def write_html_report(self, 
                         ranked_rams: pd.DataFrame,
                         cull_recommendations: pd.DataFrame,
                         config: Dict[str, Any],
                         kpis: Optional[Dict[str, Any]] = None,
                         filename: str = "analysis_report") -> Path:
        """Write comprehensive HTML report."""
        
        html_content = self._generate_html_report(
            ranked_rams, cull_recommendations, config, kpis
        )
        
        return self.write_html(html_content, filename)
    
    def _create_summary_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create summary statistics for Excel output."""
        summary_data = []
        
        if 'final_score' in df.columns:
            summary_data.append({
                'Metric': 'Total Rams',
                'Value': len(df)
            })
            summary_data.append({
                'Metric': 'Average Score',
                'Value': round(df['final_score'].mean(), 3)
            })
            summary_data.append({
                'Metric': 'Score Range',
                'Value': f"{df['final_score'].min():.3f} - {df['final_score'].max():.3f}"
            })
        
        if 'hard_filters_passed' in df.columns:
            passed = df['hard_filters_passed'].sum()
            summary_data.append({
                'Metric': 'Passed Hard Filters',
                'Value': f"{passed} / {len(df)} ({passed/len(df)*100:.1f}%)"
            })
        
        return pd.DataFrame(summary_data)
    
    def _create_cull_summary_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create cull summary statistics for Excel output."""
        summary_data = []
        
        summary_data.append({
            'Metric': 'Total Cull Recommendations',
            'Value': len(df)
        })
        
        if 'cull_reason' in df.columns:
            reason_counts = df['cull_reason'].value_counts()
            for reason, count in reason_counts.items():
                summary_data.append({
                    'Metric': f'Reason: {reason}',
                    'Value': count
                })
        
        return pd.DataFrame(summary_data)
    
    def _generate_html_report(self, 
                             ranked_rams: pd.DataFrame,
                             cull_recommendations: pd.DataFrame,
                             config: Dict[str, Any],
                             kpis: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive HTML report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sheep Data Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .table {{ border-collapse: collapse; width: 100%; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
                .config {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Sheep Data Analysis Report</h1>
                <p>Generated: {timestamp}</p>
                <p>Configuration: {config.get('name', 'Default')}</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <div class="summary">
                    <p><strong>Total Rams Analyzed:</strong> {len(ranked_rams)}</p>
                    <p><strong>Cull Recommendations:</strong> {len(cull_recommendations)}</p>
                    <p><strong>Retention Rate:</strong> {((len(ranked_rams) - len(cull_recommendations)) / len(ranked_rams) * 100):.1f}%</p>
                </div>
            </div>
        """
        
        # Add KPIs section if available
        if kpis:
            html += """
            <div class="section">
                <h2>Key Performance Indicators</h2>
                <div class="config">
            """
            for category, metrics in kpis.items():
                html += f"<h3>{category.title()}</h3><ul>"
                for metric, value in metrics.items():
                    html += f"<li><strong>{metric}:</strong> {value}</li>"
                html += "</ul>"
            html += "</div></div>"
        
        # Add configuration section
        html += """
            <div class="section">
                <h2>Configuration</h2>
                <div class="config">
        """
        for key, value in config.items():
            if isinstance(value, dict):
                html += f"<h3>{key.title()}</h3><ul>"
                for subkey, subvalue in value.items():
                    html += f"<li><strong>{subkey}:</strong> {subvalue}</li>"
                html += "</ul>"
            else:
                html += f"<p><strong>{key}:</strong> {value}</p>"
        html += "</div></div>"
        
        # Add ranked rams table
        if not ranked_rams.empty:
            html += """
            <div class="section">
                <h2>Ranked Rams</h2>
                <table class="table">
                    <thead>
                        <tr>
            """
            for col in ranked_rams.columns:
                html += f"<th>{col}</th>"
            html += """
                        </tr>
                    </thead>
                    <tbody>
            """
            for _, row in ranked_rams.head(20).iterrows():  # Show top 20
                html += "<tr>"
                for col in ranked_rams.columns:
                    html += f"<td>{row[col]}</td>"
                html += "</tr>"
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Add cull recommendations table
        if not cull_recommendations.empty:
            html += """
            <div class="section">
                <h2>Cull Recommendations</h2>
                <table class="table">
                    <thead>
                        <tr>
            """
            for col in cull_recommendations.columns:
                html += f"<th>{col}</th>"
            html += """
                        </tr>
                    </thead>
                    <tbody>
            """
            for _, row in cull_recommendations.iterrows():
                html += "<tr>"
                for col in cull_recommendations.columns:
                    html += f"<td>{row[col]}</td>"
                html += "</tr>"
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
