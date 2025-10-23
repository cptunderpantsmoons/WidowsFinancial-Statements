import streamlit as st
import io
from typing import Optional
from core.template_analyzer import TemplateAnalyzer
from core.data_handler import DataHandler
from core.ai_processor import AIProcessor
from core.pdf_handler import PDFHandler
from utils.validators import FileValidator
from utils.logger import Logger
from config.settings import ERRORS

logger = Logger(__name__)

st.set_page_config(
    page_title="Financial Statement Generator",
    page_icon="📊",
    layout="wide"
)

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
            
            ai_processor = AIProcessor()
            semantic_mapping = ai_processor.create_semantic_mapping(
                template_labels,
                data_accounts
            )
            
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
            progress_placeholder.empty()
            status_placeholder.empty()
            
            st.success("✓ PDF generated successfully!")
            
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

def main():
    """Main application."""
    initialize_session_state()
    
    st.title("📊 Financial Statement Generator")
    
    st.markdown("""
    Transform your financial statements automatically using AI-powered data mapping.
    - Upload a template PDF from a previous period
    - Provide current financial data (Excel or PDF)
    - Get a perfectly formatted PDF with new data
    
    **Privacy Notice:** Financial data is processed securely and sent to OpenRouter AI API for analysis.
    """)
    
    st.divider()
    
    if st.session_state.step == 1:
        step1_upload_template()
    elif st.session_state.step == 2:
        step2_upload_data()
    elif st.session_state.step == 3:
        step3_generate()

if __name__ == "__main__":
    main()
