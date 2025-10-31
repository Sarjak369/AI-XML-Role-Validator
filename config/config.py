# config/config.py
"""
Configuration module for AI Role Validator.
Loads all environment variables and provides centralized configuration management.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========================================
# OpenAI Configuration
# ========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate OpenAI API key presence
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Please set it in your .env file."
    )

# ========================================
# Vector Database Configuration
# ========================================
VECTOR_DB = os.getenv("VECTOR_DB", "chroma").lower()

# ChromaDB specific configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
CHROMA_COLLECTION_NAME = "role_validator"

# ========================================
# PDF Processing Configuration
# ========================================
PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", 1000))
PDF_CHUNK_OVERLAP = int(os.getenv("PDF_CHUNK_OVERLAP", 100))

# ========================================
# LLM Configuration
# ========================================
# Model selection for different tasks
# Cost-effective for role extraction
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Temperature setting for LLM responses (0.0 = deterministic)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))

# ========================================
# Role Extraction Prompt
# ========================================
DEFAULT_ROLE_PROMPT = """
Extract all job roles, job titles, or professional positions mentioned in the following document.

Instructions:
- Focus on identifying roles like "Software Engineer", "Project Manager", "Data Scientist", etc.
- Include roles from both regular text and tables
- Return ONLY a comma-separated list of unique roles
- Do NOT include explanations or additional text
- If no roles are found, respond with exactly: None

Document Content:
{document_content}

Roles (comma-separated):
"""

ROLE_EXTRACTION_PROMPT = os.getenv(
    "ROLE_EXTRACTION_PROMPT", DEFAULT_ROLE_PROMPT)

# ========================================
# Fuzzy Matching Configuration
# ========================================
# Threshold for fuzzy matching (0-100)
# Higher values require closer matches
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", 80))

# ========================================
# Retrieval Configuration
# ========================================
# Number of document chunks to retrieve for RAG
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 5))

# ========================================
# Application Settings
# ========================================
# Default XPath for XML role extraction
DEFAULT_XML_XPATH = '//role/text()'
