# app.py
"""
Streamlit web application for AI Role Validator.
Provides an interactive UI for uploading files and viewing validation results.
"""

from config.config import FUZZY_MATCH_THRESHOLD, DEFAULT_XML_XPATH
from src.role_comparer import RoleComparer
from src.pdf_extractor_rag import RAGPDFExtractor
from src.xml_parser import extract_roles_from_xml
import streamlit as st
import os
import tempfile
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Page configuration
st.set_page_config(
    page_title="AI Role Validator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None


def display_header():
    """Display application header."""
    st.title("🤖 AI Role Validator")
    st.markdown("""
    **Intelligent XML ↔ PDF Role Comparison powered by LangChain & OpenAI**
    
    This application validates job roles in PDF documents against XML-defined standards using:
    - 🔍 RAG (Retrieval-Augmented Generation)
    - 🧠 OpenAI GPT-4 for role extraction
    - 📊 ChromaDB for vector storage
    - ≈ Fuzzy matching for variations
    """)
    st.divider()


def display_sidebar():
    """Display sidebar with configuration and information."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Fuzzy matching threshold
        threshold = st.slider(
            "Fuzzy Match Threshold",
            min_value=50,
            max_value=100,
            value=FUZZY_MATCH_THRESHOLD,
            help="Minimum similarity score (0-100) for fuzzy matching"
        )

        st.divider()

        st.header("📚 How It Works")
        st.markdown("""
        1. **Upload XML** - Contains correct role definitions
        2. **Upload PDF** - Document to validate
        3. **Click Validate** - AI processes both files
        4. **View Report** - See matches and discrepancies
        
        **Matching Types:**
        - ✓ **Direct**: Exact match
        - ≈ **Fuzzy**: Similar (typos, variations)
        - ✗ **No Match**: Role not in XML
        """)

        st.divider()

        st.header("🔧 Tech Stack")
        st.markdown("""
        - **LangChain** - AI orchestration
        - **OpenAI** - LLM & embeddings
        - **ChromaDB** - Vector database
        - **PyMuPDF** - PDF extraction
        - **Streamlit** - Web interface
        """)

        return threshold


def run_validation(xml_file, pdf_file, threshold):
    """
    Executes the validation pipeline.

    Args:
        xml_file: Uploaded XML file
        pdf_file: Uploaded PDF file
        threshold: Fuzzy matching threshold

    Returns:
        dict: Validation results
    """
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_xml:
        tmp_xml.write(xml_file.getvalue())
        xml_filepath = tmp_xml.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(pdf_file.getvalue())
        pdf_filepath = tmp_pdf.name

    try:
        results = {}

        # Step 1: Extract XML roles
        with st.spinner("📝 Extracting roles from XML..."):
            xml_roles = extract_roles_from_xml(xml_filepath, DEFAULT_XML_XPATH)
            results['xml_roles'] = xml_roles

            if not xml_roles:
                st.warning("⚠️ No roles found in XML file. Check file format.")
                return None

        st.success(f"✅ Extracted {len(xml_roles)} roles from XML")

        # Step 2: Initialize PDF extractor
        with st.spinner("🔧 Initializing AI components (LangChain + ChromaDB)..."):
            pdf_extractor = RAGPDFExtractor()
            results['pdf_extractor'] = pdf_extractor

        st.success("✅ AI components initialized")

        # Step 3: Process PDF
        pdf_id = "streamlit-upload"

        with st.spinner("🗑️ Clearing previous data..."):
            pdf_extractor.clear_pdf_data(pdf_id)

        with st.spinner("📊 Indexing PDF into vector store..."):
            success = pdf_extractor.process_pdf(pdf_filepath, pdf_id)
            if not success:
                st.error("❌ Failed to process PDF")
                return None

        st.success("✅ PDF indexed successfully")

        with st.spinner("🔍 Extracting roles from PDF using AI..."):
            pdf_roles = pdf_extractor.extract_roles_from_pdf(pdf_filepath)
            results['pdf_roles'] = pdf_roles

            if not pdf_roles:
                st.warning("⚠️ No roles found in PDF. Check PDF content.")

        st.success(f"✅ Extracted {len(pdf_roles)} roles from PDF")

        # Step 4: Compare roles
        with st.spinner("⚖️ Comparing roles with fuzzy matching..."):
            comparer = RoleComparer(fuzzy_threshold=threshold)

            is_incorrect, matched_roles, incorrect_pdf_roles, fuzzy_matches = comparer.compare_roles(
                xml_roles, pdf_roles
            )

            results['is_incorrect'] = is_incorrect
            results['matched_roles'] = matched_roles
            results['incorrect_pdf_roles'] = incorrect_pdf_roles
            results['fuzzy_matches'] = fuzzy_matches
            results['comparer'] = comparer

        st.success("✅ Comparison complete")

        return results

    except Exception as e:
        st.error(f"❌ Error during validation: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

    finally:
        # Cleanup temporary files
        if os.path.exists(xml_filepath):
            os.remove(xml_filepath)
        if os.path.exists(pdf_filepath):
            os.remove(pdf_filepath)


def display_results(results):
    """
    Displays validation results in a formatted layout.

    Args:
        results: Dictionary containing validation results
    """
    st.header("📊 Validation Results")

    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="XML Roles",
            value=len(results['xml_roles'])
        )

    with col2:
        st.metric(
            label="PDF Roles",
            value=len(results['pdf_roles'])
        )

    with col3:
        st.metric(
            label="Matched",
            value=len(results['matched_roles']),
            delta="Good" if results['matched_roles'] else None
        )

    with col4:
        st.metric(
            label="Incorrect",
            value=len(results['incorrect_pdf_roles']),
            delta="Bad" if results['incorrect_pdf_roles'] else "Good",
            delta_color="inverse"
        )

    st.divider()

    # Main conclusion
    if results['is_incorrect']:
        st.error("🔴 **VALIDATION FAILED**: PDF contains incorrect roles")
    else:
        st.success("🟢 **VALIDATION PASSED**: All PDF roles match XML")

    st.divider()

    # Detailed results in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "✅ Matched Roles",
        "❌ Incorrect Roles",
        "📋 All Roles",
        "📊 Detailed Report"
    ])

    with tab1:
        st.subheader("Matched Roles")
        if results['matched_roles']:
            for role in results['matched_roles']:
                # Check if fuzzy matched
                fuzzy_match = None
                for pdf_role, xml_role in results['fuzzy_matches'].items():
                    if xml_role == role:
                        fuzzy_match = pdf_role
                        break

                if fuzzy_match:
                    st.write(f"≈ **{role}** (fuzzy matched: *{fuzzy_match}*)")
                else:
                    st.write(f"✓ **{role}**")
        else:
            st.info("No matched roles found")

    with tab2:
        st.subheader("Incorrect PDF Roles")
        if results['incorrect_pdf_roles']:
            st.warning(
                "These roles appear in the PDF but do not match any XML role, "
                "even with fuzzy matching:"
            )
            for role in results['incorrect_pdf_roles']:
                st.write(f"✗ **{role}**")
        else:
            st.success("No incorrect roles found!")

    with tab3:
        st.subheader("All Extracted Roles")

        col_xml, col_pdf = st.columns(2)

        with col_xml:
            st.markdown("**XML Roles (Ground Truth):**")
            for i, role in enumerate(results['xml_roles'], 1):
                st.write(f"{i}. {role}")

        with col_pdf:
            st.markdown("**PDF Roles (Extracted):**")
            for i, role in enumerate(results['pdf_roles'], 1):
                st.write(f"{i}. {role}")

    with tab4:
        st.subheader("Detailed Validation Report")

        # Generate text report
        report = results['comparer'].generate_report(
            is_incorrect=results['is_incorrect'],
            matched_roles=results['matched_roles'],
            incorrect_pdf_roles=results['incorrect_pdf_roles'],
            fuzzy_matches=results['fuzzy_matches'],
            xml_roles=results['xml_roles'],
            pdf_roles=results['pdf_roles']
        )

        st.code(report, language=None)

        # Download button for report
        st.download_button(
            label="📥 Download Report",
            data=report,
            file_name="validation_report.txt",
            mime="text/plain"
        )


def main():
    """Main application logic."""
    initialize_session_state()
    display_header()
    threshold = display_sidebar()

    # File upload section
    st.header("📁 Upload Files")

    col1, col2 = st.columns(2)

    with col1:
        xml_file = st.file_uploader(
            "Upload XML File (Defined Roles)",
            type=["xml"],
            help="XML file containing the correct job roles"
        )

        if xml_file:
            st.success(f"✅ {xml_file.name}")

    with col2:
        pdf_file = st.file_uploader(
            "Upload PDF File (Document to Validate)",
            type=["pdf"],
            help="PDF document containing roles to validate"
        )

        if pdf_file:
            st.success(f"✅ {pdf_file.name}")

    st.divider()

    # Validation button
    if xml_file and pdf_file:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🚀 Start Validation", type="primary", use_container_width=True):
                with st.status("Processing...", expanded=True) as status:
                    results = run_validation(xml_file, pdf_file, threshold)

                    if results:
                        st.session_state.validation_results = results
                        st.session_state.processing_complete = True
                        status.update(
                            label="✅ Validation Complete!",
                            state="complete",
                            expanded=False
                        )
    else:
        st.info("👆 Please upload both XML and PDF files to begin validation")

    # Display results if available
    if st.session_state.processing_complete and st.session_state.validation_results:
        st.divider()
        display_results(st.session_state.validation_results)

        # Optional: RAG Query Demo
        with st.expander("💬 Try RAG Query (Optional)"):
            st.markdown("""
            Ask questions about the PDF content using Retrieval-Augmented Generation.
            The AI will search the document and provide context-based answers.
            """)

            query = st.text_input(
                "Enter your question:",
                placeholder="e.g., What are the different job roles mentioned?"
            )

            if query and st.button("Ask Question"):
                with st.spinner("🔍 Searching document..."):
                    pdf_extractor = st.session_state.validation_results['pdf_extractor']
                    answer = pdf_extractor.query_pdf_with_rag(
                        query,
                        pdf_id="streamlit-upload",
                        top_k=5
                    )

                    st.markdown("**Answer:**")
                    st.info(answer)


if __name__ == "__main__":
    main()
