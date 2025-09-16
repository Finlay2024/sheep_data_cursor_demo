"""Main Streamlit application for sheep data analysis."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import logging

# Add the parent directory to the path so we can import sheepapp
sys.path.append(str(Path(__file__).parent.parent))

from sheepapp.io import DataLoader, load_demo_data
from sheepapp.processing import DataCleaner, ContemporaryGrouping, DataStandardizer
from sheepapp.metrics import MetricsCalculator
from sheepapp.scoring import ScoringEngine
from sheepapp.config_presets import ConfigPresets
from sheepapp.core.models import AnalysisConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Sheep Data Analysis",
    page_icon="🐑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'kpis' not in st.session_state:
    st.session_state.kpis = None
if 'config' not in st.session_state:
    st.session_state.config = None
if 'results' not in st.session_state:
    st.session_state.results = None

def main():
    """Main application function."""
    st.title("🐑 Sheep Data Analysis")
    st.markdown("**Rank rams for selection and recommend flock reductions**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["📤 Data Upload", "🔍 Data Quality", "📈 KPIs", "🧮 Selection Weights", 
         "🏅 Ram Results", "✂️ Cull Recommendations", "🧾 Reports & Export"]
    )
    
    # Route to appropriate page
    if page == "📤 Data Upload":
        data_upload_page()
    elif page == "🔍 Data Quality":
        data_quality_page()
    elif page == "📈 KPIs":
        kpis_page()
    elif page == "🧮 Selection Weights":
        selection_weights_page()
    elif page == "🏅 Ram Results":
        ram_results_page()
    elif page == "✂️ Cull Recommendations":
        cull_recommendations_page()
    elif page == "🧾 Reports & Export":
        reports_export_page()

def data_upload_page():
    """Data upload and validation page."""
    st.header("📤 Data Upload")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Data")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'parquet'],
            help="Upload CSV, Excel, or Parquet file with sheep data"
        )
        
        if uploaded_file is not None:
            try:
                # Load data from uploaded file
                loader = DataLoader()
                
                # Determine file type and load accordingly
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension in ['xlsx', 'xls']:
                    df = pd.read_excel(uploaded_file)
                elif file_extension == 'parquet':
                    df = pd.read_parquet(uploaded_file)
                else:
                    st.error(f"❌ Unsupported file format: {file_extension}")
                    return
                
                # Validate and clean the data
                df = loader.validate_and_clean(df, uploaded_file.name)
                
                st.session_state.data = df
                st.success(f"✅ Data loaded successfully! {len(df)} rows, {len(df.columns)} columns")
                
                # Show preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
    
    with col2:
        st.subheader("Demo Data")
        
        if st.button("🐑 Use Demo Dataset", type="primary"):
            try:
                df = load_demo_data()
                st.session_state.data = df
                st.success(f"✅ Demo data loaded! {len(df)} rows, {len(df.columns)} columns")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error loading demo data: {str(e)}")
        
        # Show data info
        if st.session_state.data is not None:
            st.subheader("Data Info")
            st.metric("Total Animals", len(st.session_state.data))
            st.metric("Columns", len(st.session_state.data.columns))
            
            # Show sex distribution
            if 'sex' in st.session_state.data.columns:
                sex_counts = st.session_state.data['sex'].value_counts()
                st.subheader("Sex Distribution")
                for sex, count in sex_counts.items():
                    st.metric(sex, count)

def data_quality_page():
    """Data quality analysis page."""
    st.header("🔍 Data Quality")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first on the Data Upload page")
        return
    
    df = st.session_state.data
    
    # Data quality overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(df))
        st.metric("Total Columns", len(df.columns))
    
    with col2:
        missing_data = df.isnull().sum().sum()
        st.metric("Missing Values", missing_data)
        st.metric("Missing %", f"{(missing_data / (len(df) * len(df.columns)) * 100):.1f}%")
    
    with col3:
        duplicates = df.duplicated().sum()
        st.metric("Duplicate Rows", duplicates)
    
    # Missing data analysis
    st.subheader("Missing Data Analysis")
    missing_df = df.isnull().sum().reset_index()
    missing_df.columns = ['Column', 'Missing Count']
    missing_df['Missing %'] = (missing_df['Missing Count'] / len(df) * 100).round(2)
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    
    if not missing_df.empty:
        st.dataframe(missing_df, use_container_width=True)
        
        # Missing data chart
        fig = px.bar(missing_df, x='Column', y='Missing %', 
                    title="Missing Data by Column")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ No missing data found!")
    
    # Data types
    st.subheader("Data Types")
    dtype_df = df.dtypes.reset_index()
    dtype_df.columns = ['Column', 'Data Type']
    st.dataframe(dtype_df, use_container_width=True)
    
    # Outlier detection
    st.subheader("Outlier Detection")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) > 0:
        outlier_col = st.selectbox("Select column for outlier analysis", numeric_cols)
        
        if outlier_col in df.columns:
            Q1 = df[outlier_col].quantile(0.25)
            Q3 = df[outlier_col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[outlier_col] < lower_bound) | (df[outlier_col] > upper_bound)]
            
            st.metric("Outliers Found", len(outliers))
            
            if len(outliers) > 0:
                st.dataframe(outliers[['animal_id', outlier_col]], use_container_width=True)
                
                # Outlier chart
                fig = px.box(df, y=outlier_col, title=f"Outlier Analysis: {outlier_col}")
                st.plotly_chart(fig, use_container_width=True)

def kpis_page():
    """KPI calculation and visualization page."""
    st.header("📈 Key Performance Indicators")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first on the Data Upload page")
        return
    
    if st.button("🔄 Calculate KPIs", type="primary"):
        with st.spinner("Calculating KPIs..."):
            try:
                # Clean data
                cleaner = DataCleaner()
                cleaned_df = cleaner.clean_data(st.session_state.data)
                
                # Create contemporary groups
                grouper = ContemporaryGrouping()
                grouped_df = grouper.create_contemporary_groups(cleaned_df)
                
                # Calculate metrics
                calculator = MetricsCalculator()
                kpis_df = calculator.calculate_all_metrics(grouped_df)
                
                st.session_state.cleaned_data = kpis_df
                st.session_state.kpis = calculator.get_metrics_summary(kpis_df)
                
                st.success("✅ KPIs calculated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error calculating KPIs: {str(e)}")
    
    if st.session_state.kpis is not None:
        st.subheader("KPI Summary")
        
        # Show metric availability
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Available Metrics:**")
            for metric, available in st.session_state.kpis['metric_availability'].items():
                status = "✅" if available else "❌"
                st.write(f"{status} {metric}")
        
        with col2:
            st.write("**Metric Statistics:**")
            for metric, stats in st.session_state.kpis['metric_statistics'].items():
                if stats['count'] > 0:
                    st.write(f"**{metric}:**")
                    st.write(f"  - Count: {stats['count']}")
                    st.write(f"  - Mean: {stats['mean']:.2f}")
                    st.write(f"  - Std: {stats['std']:.2f}")
        
        # Show KPI data
        if st.session_state.cleaned_data is not None:
            st.subheader("KPI Data")
            st.dataframe(st.session_state.cleaned_data.head(20), use_container_width=True)
            
            # Download button
            csv = st.session_state.cleaned_data.to_csv(index=False)
            st.download_button(
                label="📥 Download KPI Data (CSV)",
                data=csv,
                file_name="kpi_data.csv",
                mime="text/csv"
            )

def selection_weights_page():
    """Selection weights configuration page."""
    st.header("🧮 Selection Weights")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first on the Data Upload page")
        return
    
    # Load presets
    presets = ConfigPresets()
    available_presets = presets.get_available_presets()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configuration Presets")
        
        selected_preset = st.selectbox("Select Preset", available_presets)
        
        if st.button("📥 Load Preset"):
            try:
                config = presets.create_config_from_preset(selected_preset)
                st.session_state.config = config
                st.success(f"✅ Loaded preset: {selected_preset}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error loading preset: {str(e)}")
        
        # Preset descriptions
        st.subheader("Preset Descriptions")
        descriptions = {
            "balanced": "Equal emphasis on all traits",
            "meat": "Focus on growth and meat production",
            "wool": "Focus on wool production and quality",
            "worm": "Focus on health and worm resistance"
        }
        
        for preset in available_presets:
            if preset in descriptions:
                st.write(f"**{preset.title()}:** {descriptions[preset]}")
    
    with col2:
        st.subheader("Weight Configuration")
        
        if st.session_state.config is None:
            st.session_state.config = AnalysisConfig()
        
        # Category weights
        st.write("**Category Weights:**")
        weights = {}
        
        col_a, col_b = st.columns(2)
        with col_a:
            weights['growth'] = st.slider("Growth", 0.0, 1.0, st.session_state.config.weights['growth'], 0.05)
            weights['wool'] = st.slider("Wool", 0.0, 1.0, st.session_state.config.weights['wool'], 0.05)
            weights['reproduction'] = st.slider("Reproduction", 0.0, 1.0, st.session_state.config.weights['reproduction'], 0.05)
        
        with col_b:
            weights['health'] = st.slider("Health", 0.0, 1.0, st.session_state.config.weights['health'], 0.05)
            weights['temperament'] = st.slider("Temperament", 0.0, 1.0, st.session_state.config.weights['temperament'], 0.05)
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Show weight distribution
        st.write("**Weight Distribution:**")
        weight_df = pd.DataFrame(list(weights.items()), columns=['Category', 'Weight'])
        fig = px.pie(weight_df, values='Weight', names='Category', title="Category Weights")
        st.plotly_chart(fig, use_container_width=True)
        
        # Filter settings
        st.subheader("Filter Settings")
        
        col_c, col_d = st.columns(2)
        with col_c:
            min_birth_weight = st.number_input("Min Birth Weight (kg)", 0.0, 10.0, st.session_state.config.min_birth_weight, 0.1)
            max_footrot = st.number_input("Max Footrot Score", 0, 5, st.session_state.config.max_footrot_score, 1)
            max_dag = st.number_input("Max DAG Score", 0, 5, st.session_state.config.max_dag_score, 1)
        
        with col_d:
            min_weaning_weight = st.number_input("Min Weaning Weight (kg)", 0.0, 50.0, st.session_state.config.min_weaning_weight, 1.0)
            max_micron = st.number_input("Max Micron", 10.0, 50.0, st.session_state.config.max_micron, 0.5)
            bse_required = st.checkbox("BSE Pass Required", st.session_state.config.bse_pass_required)
        
        # Update config
        st.session_state.config.weights = weights
        st.session_state.config.min_birth_weight = min_birth_weight
        st.session_state.config.max_footrot_score = max_footrot
        st.session_state.config.max_dag_score = max_dag
        st.session_state.config.min_weaning_weight = min_weaning_weight
        st.session_state.config.max_micron = max_micron
        st.session_state.config.bse_pass_required = bse_required

def ram_results_page():
    """Ram ranking and results page."""
    st.header("🏅 Ram Results")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first on the Data Upload page")
        return
    
    if st.session_state.config is None:
        st.warning("⚠️ Please configure selection weights first")
        return
    
    if st.button("🔄 Run Analysis", type="primary"):
        with st.spinner("Running analysis..."):
            try:
                # Run complete analysis
                scoring_engine = ScoringEngine(st.session_state.config)
                results = scoring_engine.score_animals(st.session_state.data)
                
                st.session_state.results = results
                st.success("✅ Analysis completed successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error running analysis: {str(e)}")
    
    if st.session_state.results is not None:
        results = st.session_state.results
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Animals", results['filter_summary']['hard_filters']['original_count'])
        with col2:
            st.metric("After Filters", results['filter_summary']['hard_filters']['final_count'])
        with col3:
            st.metric("Rams Ranked", len(results['ranked_rams']))
        with col4:
            st.metric("Cull Recommendations", len(results['cull_candidates'][results['cull_candidates']['cull_recommended']]))
        
        # Ranked rams table
        st.subheader("Ranked Rams")
        
        if not results['ranked_rams'].empty:
            # Select columns to display
            display_cols = ['rank', 'animal_id', 'sex', 'composite_score', 'growth_score', 
                           'wool_score', 'reproduction_score', 'health_score', 'temperament_score']
            
            available_cols = [col for col in display_cols if col in results['ranked_rams'].columns]
            display_df = results['ranked_rams'][available_cols].head(20)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Score distribution chart
            fig = px.histogram(results['ranked_rams'], x='composite_score', 
                              title="Composite Score Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Category scores radar chart
            if len(results['ranked_rams']) > 0:
                top_ram = results['ranked_rams'].iloc[0]
                categories = ['growth_score', 'wool_score', 'reproduction_score', 'health_score', 'temperament_score']
                available_categories = [cat for cat in categories if cat in top_ram.index]
                
                if available_categories:
                    values = [top_ram[cat] for cat in available_categories]
                    labels = [cat.replace('_score', '').title() for cat in available_categories]
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=values,
                        theta=labels,
                        fill='toself',
                        name=f"Top Ram ({top_ram['animal_id']})"
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )),
                        showlegend=True,
                        title="Top Ram Performance Profile"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Download button
            csv = results['ranked_rams'].to_csv(index=False)
            st.download_button(
                label="📥 Download Ranked Rams (CSV)",
                data=csv,
                file_name="ranked_rams.csv",
                mime="text/csv"
            )
        else:
            st.warning("No rams found in the dataset")

def cull_recommendations_page():
    """Cull recommendations page."""
    st.header("✂️ Cull Recommendations")
    
    if st.session_state.results is None:
        st.warning("⚠️ Please run analysis first on the Ram Results page")
        return
    
    results = st.session_state.results
    cull_candidates = results['cull_candidates']
    
    # Cull summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Animals", len(cull_candidates))
    with col2:
        st.metric("Cull Recommended", cull_candidates['cull_recommended'].sum())
    with col3:
        st.metric("Retention Rate", f"{(1 - cull_candidates['cull_recommended'].sum() / len(cull_candidates)) * 100:.1f}%")
    
    # Cull recommendations table
    st.subheader("Cull Recommendations")
    
    cull_df = cull_candidates[cull_candidates['cull_recommended'] == True]
    
    if not cull_df.empty:
        # Select columns to display
        display_cols = ['animal_id', 'sex', 'cull_reasons', 'composite_score', 'rank']
        available_cols = [col for col in display_cols if col in cull_df.columns]
        display_df = cull_df[available_cols]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Cull reasons analysis
        if 'cull_reasons' in cull_df.columns:
            st.subheader("Cull Reasons Analysis")
            
            # Count reasons
            all_reasons = []
            for reasons in cull_df['cull_reasons']:
                if pd.notna(reasons) and reasons != '':
                    all_reasons.extend([r.strip() for r in reasons.split(';')])
            
            if all_reasons:
                reason_counts = pd.Series(all_reasons).value_counts()
                
                fig = px.bar(x=reason_counts.index, y=reason_counts.values,
                            title="Cull Reasons Distribution")
                fig.update_xaxis(title="Reason")
                fig.update_yaxis(title="Count")
                st.plotly_chart(fig, use_container_width=True)
        
        # Download button
        csv = cull_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Cull Recommendations (CSV)",
            data=csv,
            file_name="cull_recommendations.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ No cull recommendations - all animals meet selection criteria!")

def reports_export_page():
    """Reports and export page."""
    st.header("🧾 Reports & Export")
    
    if st.session_state.results is None:
        st.warning("⚠️ Please run analysis first on the Ram Results page")
        return
    
    results = st.session_state.results
    
    # Export options
    st.subheader("Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Generate HTML Report", type="primary"):
            with st.spinner("Generating HTML report..."):
                try:
                    from sheepapp.io.writers import ReportWriter
                    
                    writer = ReportWriter()
                    
                    # Generate HTML report
                    html_path = writer.write_html_report(
                        results['ranked_rams'],
                        results['cull_candidates'][results['cull_candidates']['cull_recommended'] == True],
                        results['config_used']
                    )
                    
                    st.success(f"✅ HTML report generated: {html_path}")
                    
                    # Read and display the HTML
                    with open(html_path, 'r') as f:
                        html_content = f.read()
                    
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=html_content,
                        file_name="sheep_analysis_report.html",
                        mime="text/html"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error generating HTML report: {str(e)}")
    
    with col2:
        if st.button("📈 Export All Results"):
            with st.spinner("Exporting results..."):
                try:
                    from sheepapp.scoring import ScoringEngine
                    
                    scoring_engine = ScoringEngine(st.session_state.config)
                    scoring_engine.scoring_results = results
                    
                    exported_files = scoring_engine.export_results()
                    
                    st.success(f"✅ Exported {len(exported_files)} files")
                    
                    for file_type, file_path in exported_files.items():
                        st.write(f"**{file_type}:** {file_path}")
                    
                except Exception as e:
                    st.error(f"❌ Error exporting results: {str(e)}")
    
    # Analysis summary
    st.subheader("Analysis Summary")
    
    summary = {
        "Total Animals Processed": results['filter_summary']['hard_filters']['original_count'],
        "Animals After Hard Filters": results['filter_summary']['hard_filters']['final_count'],
        "Rams Ranked": len(results['ranked_rams']),
        "Cull Recommendations": len(results['cull_candidates'][results['cull_candidates']['cull_recommended']]),
        "Retention Rate": f"{(1 - results['cull_candidates']['cull_recommended'].sum() / len(results['cull_candidates'])) * 100:.1f}%"
    }
    
    for key, value in summary.items():
        st.metric(key, value)
    
    # Configuration used
    st.subheader("Configuration Used")
    config_df = pd.DataFrame(list(results['config_used'].items()), columns=['Parameter', 'Value'])
    st.dataframe(config_df, use_container_width=True)
    
    # Clear session button
    st.subheader("Session Management")
    if st.button("🗑️ Clear Session Data", type="secondary"):
        for key in ['data', 'cleaned_data', 'kpis', 'config', 'results']:
            st.session_state[key] = None
        st.success("✅ Session data cleared")
        st.rerun()

if __name__ == "__main__":
    main()
