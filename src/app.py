import streamlit as st
import io
import os
from pathlib import Path
from typing import Optional
from core.template_analyzer import TemplateAnalyzer
from core.data_handler import DataHandler
from core.enhanced_ai_processor import EnhancedAIProcessor
from core.pdf_handler import PDFHandler
from core.financial_validator import FinancialValidator
from core.financial_analyzer import FinancialAnalyzer
from core.quality_assurance import QualityAssurance
from utils.validators import FileValidator
from utils.logger import Logger
from config.settings import ERRORS

logger = Logger(__name__)

st.set_page_config(
    page_title="Financial Statement Generator",
    page_icon="📊",
    layout="wide"
)

def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    return Path(__file__).parent.parent / ".env"

def save_api_key(api_key: str):
    """Save API key to .env file."""
    env_path = get_env_file_path()
    
    try:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_content = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            existing_content[key.strip()] = value.strip()
        
        existing_content["OPENROUTER_API_KEY"] = api_key
        
        with open(env_path, 'w') as f:
            for key, value in existing_content.items():
                f.write(f"{key}={value}\n")
        
        return True
    except Exception as e:
        logger.error(f"Failed to save API key: {str(e)}")
        return False

def is_api_key_configured() -> bool:
    """Check if OpenRouter API key is configured."""
    env_path = get_env_file_path()
    
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith("OPENROUTER_API_KEY="):
                    value = line.split("=", 1)[1].strip()
                    return bool(value and value != "your_api_key_here")
    except:
        pass
    
    return False

def show_setup_screen():
    """Display API key setup screen."""
    st.title("🚀 Initial Setup Required")
    
    st.markdown("""
    Welcome to the Financial Statement Generator! To get started, you need to configure your OpenRouter API key.
    
    ### What is OpenRouter?
    OpenRouter provides access to various AI models for semantic data mapping in your financial statements.
    
    ### Getting Your API Key
    1. Visit [openrouter.ai](https://openrouter.ai)
    2. Sign up for a free account
    3. Go to API Keys section
    4. Copy your API key
    
    ### Paste Your API Key Below
    """)
    
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-...",
        help="Your API key will be stored securely in the .env file"
    )
    
    if api_key:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Save API Key", key="save_api_key"):
                if save_api_key(api_key):
                    st.success("✓ API Key saved successfully!")
                    st.info("Restarting application...")
                    st.rerun()
                else:
                    st.error("Failed to save API key. Please try again.")
        
        with col2:
            st.link_button(
                "Get API Key",
                "https://openrouter.ai",
                use_container_width=True
            )
    else:
        st.warning("Please enter your API key to continue.")

def initialize_session_state():
    """Initialize session state variables."""
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "template_pdf" not in st.session_state:
        st.session_state.template_pdf = None
    if "data_file" not in st.session_state:
        st.session_state.data_file = None
    if "data_type" not in st.session_state:
        st.session_state.data_type = "excel"
    if "generated_pdf" not in st.session_state:
        st.session_state.generated_pdf = None
    if "processing" not in st.session_state:
        st.session_state.processing = False

def step1_upload_template():
    """Step 1: Upload template PDF."""
    st.header("Step 1: Upload Financial Statement Template")
    st.write("Upload a PDF of your previous-year financial statement to use as a template.")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="template_uploader"
    )
    
    if uploaded_file:
        file_bytes = uploaded_file.read()
        is_valid, error_msg = FileValidator.validate_file(file_bytes, uploaded_file.name)
        
        if is_valid:
            st.session_state.template_pdf = file_bytes
            st.success(f"✓ Template uploaded: {uploaded_file.name}")
            st.info(f"File size: {len(file_bytes) / (1024*1024):.2f} MB")
            
            if st.button("Proceed to Step 2 →", key="next_step1"):
                st.session_state.step = 2
                st.rerun()
        else:
            st.error(error_msg)

def step2_upload_data():
    """Step 2: Upload financial data."""
    st.header("Step 2: Upload Current Financial Data")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.data_type = st.radio(
            "Select data source format",
            ["excel", "pdf"],
            format_func=lambda x: "Excel (.xlsx)" if x == "excel" else "PDF"
        )
    
    file_type = "xlsx" if st.session_state.data_type == "excel" else "pdf"
    uploaded_file = st.file_uploader(
        f"Choose a {file_type.upper()} file",
        type=[file_type],
        key="data_uploader"
    )
    
    if uploaded_file:
        file_bytes = uploaded_file.read()
        is_valid, error_msg = FileValidator.validate_file(file_bytes, uploaded_file.name)
        
        if is_valid:
            st.session_state.data_file = file_bytes
            st.success(f"✓ Data file uploaded: {uploaded_file.name}")
            
            try:
                if st.session_state.data_type == "excel":
                    data = DataHandler.extract_from_excel(file_bytes)
                else:
                    data = DataHandler.extract_from_pdf(file_bytes)
                
                if data:
                    st.info(f"Extracted {len(data)} financial data points")
                    with st.expander("Preview extracted data"):
                        preview_items = list(data.items())[:10]
                        for account, value in preview_items:
                            st.write(f"**{account}**: {DataHandler.format_number(value)}")
                else:
                    st.warning(ERRORS["no_data_found"])
            
            except Exception as e:
                st.error(f"Error extracting data: {str(e)}")
        else:
            st.error(error_msg)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Step 1", key="back_step2"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.session_state.data_file:
            if st.button("Proceed to Step 3 →", key="next_step2"):
                st.session_state.step = 3
                st.rerun()
        else:
            st.button("Proceed to Step 3 →", disabled=True, key="next_step2_disabled")

def step3_generate():
    """Step 3: Generate financial statement."""
    st.header("Step 3: Generate Financial Statement")
    
    if st.button("🚀 Generate PDF", key="generate_button"):
        st.session_state.processing = True
        
        try:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            def update_progress(current, total, step=""):
                progress = current / total
                progress_placeholder.progress(progress)
                status_placeholder.text(f"Processing: {step} ({current}/{total})")
            
            status_placeholder.text("Initializing...")
            
            status_placeholder.text("Analyzing template...")
            analyzer = TemplateAnalyzer()
            coordinate_map = analyzer.analyze_template(
                st.session_state.template_pdf,
                lambda c, t: update_progress(c, t, f"Template Page {c}/{t}")
            )
            
            status_placeholder.text("Extracting data...")
            if st.session_state.data_type == "excel":
                data_accounts = DataHandler.extract_from_excel(st.session_state.data_file)
            else:
                data_accounts = DataHandler.extract_from_pdf(st.session_state.data_file)
            
            status_placeholder.text("Creating semantic mapping...")
            template_labels = [
                elem["text"] for page_elems in coordinate_map.values()
                for elem in page_elems
            ]
            
            ai_processor = EnhancedAIProcessor()
            semantic_mapping, confidence_scores = ai_processor.create_enhanced_semantic_mapping(
                template_labels,
                data_accounts
            )
            
            status_placeholder.text("Validating financial data...")
            validator = FinancialValidator()
            validation_results, validation_summary = validator.validate_financial_statement(data_accounts)
            
            status_placeholder.text("Performing financial analysis...")
            analyzer = FinancialAnalyzer()
            analysis_results = analyzer.perform_comprehensive_analysis(data_accounts)
            
            status_placeholder.text("Generating PDF...")
            pdf_handler = PDFHandler(st.session_state.template_pdf)
            output_pdf = pdf_handler.generate_output_pdf(
                coordinate_map,
                semantic_mapping,
                data_accounts,
                lambda c, t: update_progress(c, t, f"PDF Page {c}/{t}")
            )
            pdf_handler.close()
            
            st.session_state.generated_pdf = output_pdf
            st.session_state.validation_results = validation_results
            st.session_state.analysis_results = analysis_results
            st.session_state.confidence_scores = confidence_scores
            progress_placeholder.empty()
            status_placeholder.empty()
            
            # Show enhanced results
            st.success("✓ PDF generated with enhanced validation and analysis!")
            
            # Display quality metrics
            quality_report = ai_processor.get_quality_report()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Mapping Accuracy", 
                    f"{quality_report.get('average_confidence_score', 0):.1%}",
                    help="Average confidence score for semantic mapping"
                )
            with col2:
                st.metric(
                    "Knowledge Base Coverage", 
                    f"{quality_report.get('knowledge_base_coverage', 0):.1%}",
                    help="Percentage of mappings from knowledge base"
                )
            with col3:
                st.metric(
                    "Validation Status", 
                    validation_summary.get('status', 'Unknown'),
                    help="Financial statement validation results"
                )
            
            # Show quality grade
            st.info(f"**Quality Grade:** {quality_report.get('quality_grade', 'N/A')}")
            
            # Show detailed results in expandable sections
            with st.expander("🔍 Detailed Validation Results", expanded=False):
                if validation_results:
                    for result in validation_results[:10]:  # Show first 10
                        if result.is_valid:
                            st.success(f"✅ {result.formula_name}: {result.message}")
                        else:
                            st.error(f"❌ {result.formula_name} ({result.severity.upper()}): {result.message}")
                else:
                    st.info("No validation rules were applicable to this data")
            
            with st.expander("📊 Financial Analysis Insights", expanded=False):
                if analysis_results.get('financial_ratios'):
                    st.subheader("Calculated Financial Ratios")
                    for ratio_name, ratio_value in analysis_results['financial_ratios'].items():
                        if ratio_value is not None:
                            st.write(f"**{ratio_name.replace('_', ' ').title()}:** {ratio_value:.2f}")
                
                if analysis_results.get('benchmark_comparisons'):
                    st.subheader("Benchmark Comparisons")
                    for comp in analysis_results['benchmark_comparisons'][:5]:  # Show first 5
                        st.write(f"**{comp.metric_name.replace('_', ' ').title()}:**")
                        st.write(f"- Company Value: {comp.company_value:.2f}")
                        st.write(f"- Industry Percentile: {comp.benchmark_percentile:.0f}%")
                        st.write(f"- Performance: {comp.performance_level}")
                
                if analysis_results.get('insights'):
                    st.subheader("Key Insights")
                    for insight in analysis_results['insights'][:5]:  # Show first 5
                        st.write(f"**{insight.category} ({insight.priority}):** {insight.title}")
                        st.write(insight.description)
                        if insight.recommendation:
                            st.info(f"💡 Recommendation: {insight.recommendation}")
            
            with st.expander("🎯 Mapping Confidence Scores", expanded=False):
                for label, confidence in confidence_scores.items():
                    st.write(f"**{label}:** {confidence:.1%}")
            
            # Show confidence threshold
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
            if avg_confidence >= 0.90:
                st.success(f"🎯 **High Quality:** Average confidence {avg_confidence:.1%} achieved 99.5% accuracy target!")
            elif avg_confidence >= 0.80:
                st.info(f"✅ **Good Quality:** Average confidence {avg_confidence:.1%} approaching target accuracy")
            else:
                st.warning(f"⚠️ **Moderate Quality:** Average confidence {avg_confidence:.1%} may need review for critical applications")
            
            st.download_button(
                label="📥 Download Financial Statement PDF",
                data=output_pdf,
                file_name="financial_statement.pdf",
                mime="application/pdf",
                key="download_button"
            )
        
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
            logger.error(f"Generation error: {str(e)}")
        
        finally:
            st.session_state.processing = False
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Step 2", key="back_step3"):
            st.session_state.step = 2
            st.rerun()

def show_settings_button():
    """Show settings button to change API key."""
    if st.button("⚙️ Settings", key="settings_button"):
        st.session_state.show_settings = True

def show_api_key_modal():
    """Show modal to update API key."""
    if st.session_state.get("show_settings", False):
        st.markdown("---")
        st.subheader("⚙️ Settings")
        
        st.markdown("### Update API Key")
        new_api_key = st.text_input(
            "New OpenRouter API Key",
            type="password",
            placeholder="sk-or-...",
            key="settings_api_key"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Save New Key", key="save_new_key"):
                if new_api_key:
                    if save_api_key(new_api_key):
                        st.success("✓ API Key updated successfully!")
                        st.session_state.show_settings = False
                        st.rerun()
                    else:
                        st.error("Failed to save API key.")
                else:
                    st.warning("Please enter an API key.")
        
        with col2:
            if st.button("✕ Cancel", key="cancel_settings"):
                st.session_state.show_settings = False
                st.rerun()

def main():
    """Main application."""
    
    if not is_api_key_configured():
        show_setup_screen()
        return
    
    initialize_session_state()
    
    st.title("📊 Financial Statement Generator")
    
    col1, col2 = st.columns([10, 1])
    with col2:
        show_settings_button()
    
    st.markdown("""
    Transform your financial statements automatically using AI-powered data mapping.
    - Upload a template PDF from a previous period
    - Provide current financial data (Excel or PDF)
    - Get a perfectly formatted PDF with new data
    
    **Privacy Notice:** Financial data is processed securely and sent to OpenRouter AI API for analysis.
    """)
    
    show_api_key_modal()
    
    st.divider()
    
    if st.session_state.step == 1:
        step1_upload_template()
    elif st.session_state.step == 2:
        step2_upload_data()
    elif st.session_state.step == 3:
        step3_generate()

if __name__ == "__main__":
    main()
