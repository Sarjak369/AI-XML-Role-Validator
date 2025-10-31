# src/pdf_extractor_rag.py
"""
PDF extractor with RAG (Retrieval-Augmented Generation) capabilities.
Handles PDF text extraction, chunking, vector storage, and role extraction.
"""

import fitz  # PyMuPDF
import uuid
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.langchain_client import LangChainClient
from src.vectorstore_client import VectorStoreClient
from src.utils import clean_extracted_roles
from config.config import PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP


class RAGPDFExtractor:
    """
    Handles PDF processing with RAG capabilities.

    Features:
    - Extract text and tables from PDFs
    - Chunk documents intelligently
    - Store chunks in vector database
    - Extract roles using LLM with RAG
    - Query documents using semantic search
    """

    def __init__(self):
        """
        Initialize RAG PDF Extractor with LangChain and vector store.
        """
        # Initialize LangChain client for LLM and embeddings
        self.langchain_client = LangChainClient()

        # Initialize vector store with embeddings function
        self.vectorstore_client = VectorStoreClient(
            embeddings_function=self.langchain_client.embeddings
        )

        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=PDF_CHUNK_SIZE,
            chunk_overlap=PDF_CHUNK_OVERLAP,
            length_function=len,
            # Split on paragraphs first
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        print("✅ RAG PDF Extractor initialized")

    def _extract_text_and_tables_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text content from a PDF file, including tables.

        Uses PyMuPDF (fitz) to extract:
        - Text blocks
        - Tables (structured data)
        - Preserves formatting for better context
        """
        full_text = []

        try:
            pdf_document = fitz.open(pdf_path)
            print(
                f"📄 Processing PDF: {pdf_path} ({pdf_document.page_count} pages)")

            # Iterate through all pages
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)

                # --- Extract text blocks ---
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    text_content = block[4].strip()
                    if text_content:
                        full_text.append(text_content)

                # --- Extract tables (new API) ---
                try:
                    # type: ignore[attr-defined]
                    table_finder = page.find_tables()  # type:ignore
                    tables = getattr(table_finder, "tables", [])
                except Exception:
                    tables = []

                if tables:
                    for table in tables:
                        table_rows = []
                        for row_data in table.extract():
                            row_text = " | ".join([
                                str(cell) if cell is not None else ""
                                for cell in row_data
                            ])
                            table_rows.append(row_text)

                        # Format table nicely
                        table_str = "\n".join(table_rows)
                        formatted_table = (
                            f"\n--- TABLE: ROLES AND INFORMATION ---\n"
                            f"{table_str.strip()}\n"
                            f"--- END OF TABLE ---\n"
                        )
                        full_text.append(formatted_table)

            pdf_document.close()

            full_document_text = "\n\n".join(full_text)

            print(f"✅ Extracted {len(full_document_text)} characters from PDF")
            if 'tables' in locals():
                print(f"📊 Found {len(tables)} tables")

            return full_document_text

        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return ""

    def process_pdf(self, pdf_path: str, pdf_id: str) -> bool:
        """
        Processes PDF: extracts text, chunks it, and stores in vector database.

        This is the main method for indexing a PDF for RAG.

        Args:
            pdf_path (str): Path to the PDF file
            pdf_id (str): Unique identifier for this PDF

        Returns:
            bool: Success status
        """
        print(f"\n🔄 Processing PDF: {pdf_path}")

        # Extract text from PDF
        text = self._extract_text_and_tables_from_pdf(pdf_path)

        if not text.strip():
            print(
                f"⚠️  No content extracted from {pdf_path}. Skipping indexing.")
            return False

        # Split text into chunks using LangChain's text splitter
        chunks = self.text_splitter.split_text(text)
        print(f"✂️  Split document into {len(chunks)} chunks")

        if not chunks:
            print("⚠️  No chunks created. Skipping indexing.")
            return False

        # Prepare data for vector store
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        for i, chunk in enumerate(chunks):
            # Generate unique ID for each chunk
            chunk_id = f"{pdf_id}-{uuid.uuid4().hex[:8]}-chunk{i}"

            # Store chunk with metadata
            chunk_texts.append(chunk)
            chunk_metadatas.append({
                "pdf_id": pdf_id,
                "chunk_index": i,
                "chunk_id": chunk_id,
                "source": pdf_path
            })
            chunk_ids.append(chunk_id)

        # Add documents to vector store
        added_ids = self.vectorstore_client.add_documents(
            texts=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )

        if added_ids:
            print(
                f"✅ Successfully indexed {len(added_ids)} chunks for PDF: {pdf_id}")
            return True
        else:
            print(f"❌ Failed to index chunks for PDF: {pdf_id}")
            return False

    def extract_roles_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extracts job roles from PDF using LLM.

        This method:
        1. Extracts full text from PDF
        2. Sends text to LLM with role extraction prompt
        3. Parses and cleans the LLM response

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            List[str]: List of unique job roles found
        """
        print(f"\n🔍 Extracting roles from PDF: {pdf_path}")

        # Extract full text from PDF
        extracted_text = self._extract_text_and_tables_from_pdf(pdf_path)

        if not extracted_text.strip():
            print(
                f"⚠️  No content extracted from {pdf_path} for role extraction.")
            return []

        # Use LLM to extract roles
        raw_roles_str = self.langchain_client.extract_roles_from_text(
            extracted_text)

        # Clean and parse the LLM response
        roles = clean_extracted_roles(raw_roles_str)

        if roles:
            print(f"✅ Extracted {len(roles)} unique roles from PDF")
            print(f"📋 Roles: {', '.join(roles)}")
        else:
            print("⚠️  No roles found in PDF")

        return roles

    def query_pdf_with_rag(
        self,
        query: str,
        pdf_id: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Queries the PDF content using RAG.

        This demonstrates the RAG pipeline:
        1. User asks a question
        2. Retrieve relevant chunks from vector store
        3. Pass chunks to LLM as context
        4. LLM answers based on retrieved context

        Args:
            query (str): The question to ask
            pdf_id (Optional[str]): Filter by specific PDF ID
            top_k (int): Number of chunks to retrieve

        Returns:
            str: Answer generated by LLM
        """
        print(f"\n🔍 RAG Query: {query}")

        # Build filter for specific PDF if provided
        filter_dict = {"pdf_id": pdf_id} if pdf_id else None

        # Retrieve relevant documents
        results = self.vectorstore_client.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filter_dict
        )

        if not results:
            return "No relevant information found in the PDF documents."

        # Log retrieved chunks for debugging
        print(f"📚 Retrieved {len(results)} relevant chunks:")
        for i, (doc, score) in enumerate(results, 1):
            print(
                f"  {i}. Score: {score:.3f}, Content: {doc.page_content[:100]}...")

        # Combine retrieved contexts
        context = "\n\n".join([doc.page_content for doc, _ in results])

        # Generate answer using LLM with context
        answer = self.langchain_client.query_with_context(query, context)

        print(f"💬 Answer: {answer[:200]}...")

        return answer

    def clear_pdf_data(self, pdf_id: str) -> bool:
        """
        Deletes all data associated with a specific PDF ID.

        Useful for cleaning up before reprocessing a PDF.

        Args:
            pdf_id (str): The PDF identifier to clear

        Returns:
            bool: Success status
        """
        print(f"🗑️  Clearing data for PDF ID: {pdf_id}")

        success = self.vectorstore_client.delete_by_filter({"pdf_id": pdf_id})

        if success:
            print(f"✅ Cleared all data for PDF ID: {pdf_id}")
        else:
            print(f"⚠️  No data found for PDF ID: {pdf_id}")

        return success

    def get_pdf_statistics(self, pdf_id: str) -> Dict:
        """
        Returns statistics about indexed PDF data.

        Args:
            pdf_id (str): The PDF identifier

        Returns:
            Dict: Statistics about the PDF's indexed data
        """
        documents = self.vectorstore_client.get_documents_by_pdf_id(pdf_id)

        if not documents:
            return {
                "pdf_id": pdf_id,
                "chunk_count": 0,
                "status": "not_found"
            }

        total_chars = sum(len(doc.page_content) for doc in documents)

        return {
            "pdf_id": pdf_id,
            "chunk_count": len(documents),
            "total_characters": total_chars,
            "average_chunk_size": total_chars // len(documents) if documents else 0,
            "status": "indexed"
        }

    def clear_all_data(self) -> bool:
        """
        Clears all data from the vector store.

        Use with caution - this deletes everything!

        Returns:
            bool: Success status
        """
        print("⚠️  WARNING: Clearing ALL data from vector store")
        return self.vectorstore_client.clear_collection()
