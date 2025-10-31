# src/main.py
"""
Command-line interface for the AI Role Validator.
Runs the complete validation pipeline without Streamlit UI.
"""

from config.config import (
    FUZZY_MATCH_THRESHOLD,
    DEFAULT_XML_XPATH,
    CHROMA_PERSIST_DIR
)
from src.role_comparer import RoleComparer
from src.pdf_extractor_rag import RAGPDFExtractor
from src.xml_parser import extract_roles_from_xml
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def ensure_data_directories():
    """
    Ensures that required data directories exist.
    Creates them if they don't exist.
    """
    directories = [
        'data/xml_data',
        'data/pdf_data',
        CHROMA_PERSIST_DIR
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory ready: {directory}")


def create_sample_xml(xml_filepath: str):
    """
    Creates a sample XML file with job roles if it doesn't exist.

    Args:
        xml_filepath (str): Path where XML file should be created
    """
    if os.path.exists(xml_filepath):
        print(f"✓ XML file already exists: {xml_filepath}")
        return

    sample_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<roles>
    <role>Software Engineer</role>
    <role>Project Manager</role>
    <role>Senior Developer</role>
    <role>QA Tester</role>
    <role>Business Analyst</role>
    <role>Data Scientist</role>
</roles>"""

    with open(xml_filepath, 'w', encoding='utf-8') as f:
        f.write(sample_xml_content)

    print(f"✅ Created sample XML file: {xml_filepath}")


def validate_pdf_exists(pdf_filepath: str) -> bool:
    """
    Validates that the PDF file exists.

    Args:
        pdf_filepath (str): Path to PDF file

    Returns:
        bool: True if file exists, False otherwise
    """
    if not os.path.exists(pdf_filepath):
        print("\n" + "=" * 60)
        print("⚠️  PDF FILE NOT FOUND")
        print("=" * 60)
        print(f"Expected location: {pdf_filepath}")
        print("\nPlease place a PDF file with job roles at this location.")
        print("\nExample PDF content:")
        print("  'Our team includes a Software Engineer, Project Manager,")
        print("   and Senior Developer. We also need a QA Tester and a")
        print("   Business Analyst for the upcoming project.'")
        print("\nYou can create a simple PDF using:")
        print("  • Microsoft Word (Save as PDF)")
        print("  • Google Docs (Download as PDF)")
        print("  • Any text editor with PDF export")
        print("=" * 60 + "\n")
        return False

    return True


def main():
    """
    Main execution function for the role validation pipeline.
    """
    print("\n" + "=" * 60)
    print("    🤖 AI ROLE VALIDATOR - CLI MODE")
    print("=" * 60)

    # --- Configuration ---
    xml_filepath = os.path.join('data', 'xml_data', 'defined_roles.xml')
    pdf_filepath = os.path.join('data', 'pdf_data', 'document_with_roles.pdf')
    xml_role_xpath = DEFAULT_XML_XPATH
    pdf_id = "main-document-001"

    # --- Setup ---
    print("\n📂 Setting up directories...")
    ensure_data_directories()

    print("\n📝 Preparing XML file...")
    create_sample_xml(xml_filepath)

    print("\n📄 Validating PDF file...")
    if not validate_pdf_exists(pdf_filepath):
        print("❌ Exiting: PDF file not found")
        return

    print(f"✅ Using PDF file: {pdf_filepath}")

    # --- Step 1: Extract roles from XML ---
    print("\n" + "=" * 60)
    print("STEP 1: EXTRACTING ROLES FROM XML")
    print("=" * 60)

    xml_roles = extract_roles_from_xml(xml_filepath, xml_role_xpath)

    if not xml_roles:
        print("⚠️  Warning: No roles extracted from XML.")
        print("   Please check the XML file and XPath expression.")
        return

    print(f"\n📋 Extracted {len(xml_roles)} roles from XML:")
    for i, role in enumerate(xml_roles, 1):
        print(f"  {i}. {role}")

    # --- Step 2: Initialize RAG PDF Extractor ---
    print("\n" + "=" * 60)
    print("STEP 2: INITIALIZING PDF EXTRACTOR & VECTOR STORE")
    print("=" * 60)

    pdf_extractor = RAGPDFExtractor()

    # --- Step 3: Process PDF ---
    print("\n" + "=" * 60)
    print("STEP 3: PROCESSING PDF DOCUMENT")
    print("=" * 60)

    # Clear previous data for this PDF
    print(f"\n🗑️  Clearing previous data for PDF ID: {pdf_id}")
    pdf_extractor.clear_pdf_data(pdf_id)

    # Process and index PDF
    print(f"\n📊 Indexing PDF into vector store...")
    success = pdf_extractor.process_pdf(pdf_filepath, pdf_id)

    if not success:
        print("❌ Failed to process PDF. Exiting.")
        return

    # Extract roles from PDF
    print(f"\n🔍 Extracting roles from PDF using LLM...")
    pdf_roles = pdf_extractor.extract_roles_from_pdf(pdf_filepath)

    if not pdf_roles:
        print("⚠️  Warning: No roles extracted from PDF.")
        print("   This might indicate:")
        print("   • PDF has no job roles")
        print("   • PDF content is unreadable")
        print("   • LLM prompt needs adjustment")
    else:
        print(f"\n📋 Extracted {len(pdf_roles)} roles from PDF:")
        for i, role in enumerate(pdf_roles, 1):
            print(f"  {i}. {role}")

    # --- Step 4: Compare Roles ---
    print("\n" + "=" * 60)
    print("STEP 4: COMPARING ROLES")
    print("=" * 60)

    comparer = RoleComparer(fuzzy_threshold=FUZZY_MATCH_THRESHOLD)

    is_incorrect, matched_roles, incorrect_pdf_roles, fuzzy_matches = comparer.compare_roles(
        xml_roles, pdf_roles
    )

    # --- Step 5: Generate Report ---
    print("\n" + "=" * 60)
    print("STEP 5: VALIDATION REPORT")
    print("=" * 60)

    comparer.print_report(
        is_incorrect=is_incorrect,
        matched_roles=matched_roles,
        incorrect_pdf_roles=incorrect_pdf_roles,
        fuzzy_matches=fuzzy_matches,
        xml_roles=xml_roles,
        pdf_roles=pdf_roles
    )

    # --- Optional: Demonstrate RAG Query ---
    print("\n" + "=" * 60)
    print("OPTIONAL: RAG QUERY DEMONSTRATION")
    print("=" * 60)

    print("\n💬 Testing RAG query on PDF content...")
    query = "What are the different job roles mentioned in the document?"
    answer = pdf_extractor.query_pdf_with_rag(query, pdf_id=pdf_id, top_k=5)

    print(f"\n❓ Query: {query}")
    print(f"💡 Answer: {answer}")

    # --- Statistics ---
    stats = pdf_extractor.get_pdf_statistics(pdf_id)
    print(f"\n📊 PDF Statistics:")
    print(f"  • Chunks indexed: {stats.get('chunk_count', 0)}")
    print(f"  • Total characters: {stats.get('total_characters', 0)}")
    print(f"  • Average chunk size: {stats.get('average_chunk_size', 0)}")

    # --- Completion ---
    print("\n" + "=" * 60)
    print("✅ VALIDATION COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
