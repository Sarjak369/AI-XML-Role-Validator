# Helpers (chunking, normalization, fuzzy logic)
# src/utils.py
"""
Utility functions for the AI Role Validator.
Provides text normalization, fuzzy matching, and text chunking utilities.
"""

import re
from typing import List
from thefuzz import fuzz


def normalize_role(role_name: str) -> str:
    """
    Normalizes a role name for consistent comparison.

    Normalization steps:
    1. Convert to lowercase
    2. Strip leading/trailing whitespace
    3. Remove non-alphanumeric characters (except spaces)
    4. Collapse multiple spaces into single space

    Args:
        role_name (str): The role name to normalize

    Returns:
        str: Normalized role name

    Examples:
        >>> normalize_role("Software Engineer!")
        'software engineer'
        >>> normalize_role("  Senior-Developer  ")
        'senior developer'
    """
    if not isinstance(role_name, str):
        return ""

    # Convert to lowercase and strip whitespace
    normalized = role_name.lower().strip()

    # Remove non-alphanumeric characters except whitespace
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Collapse multiple spaces into single space
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def fuzzy_match(str1: str, str2: str, threshold: int) -> bool:
    """
    Performs fuzzy string matching between two strings.

    Uses the Levenshtein distance-based ratio from thefuzz library.
    This helps catch typos, abbreviations, and minor variations.

    Args:
        str1 (str): First string to compare
        str2 (str): Second string to compare
        threshold (int): Minimum similarity score (0-100) to consider a match

    Returns:
        bool: True if similarity >= threshold, False otherwise

    Examples:
        >>> fuzzy_match("Software Engineer", "Software Eng", 80)
        True
        >>> fuzzy_match("Manager", "Developer", 80)
        False
    """
    # Calculate similarity ratio (0-100)
    similarity = fuzz.ratio(str1, str2)

    return similarity >= threshold


def fuzzy_partial_match(str1: str, str2: str, threshold: int) -> bool:
    """
    Performs partial fuzzy matching (substring matching).

    Useful for catching abbreviations like "Software Eng" in "Software Engineer".

    Args:
        str1 (str): First string to compare
        str2 (str): Second string to compare
        threshold (int): Minimum similarity score (0-100) to consider a match

    Returns:
        bool: True if partial similarity >= threshold, False otherwise
    """
    similarity = fuzz.partial_ratio(str1, str2)

    return similarity >= threshold


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Splits text into overlapping chunks for processing.

    This is essential for RAG pipelines where documents need to be
    broken into manageable pieces for embedding and retrieval.

    Args:
        text (str): The text to chunk
        chunk_size (int): Maximum size of each chunk in characters
        overlap (int): Number of overlapping characters between chunks

    Returns:
        List[str]: List of text chunks

    Examples:
        >>> chunks = chunk_text("Hello World!", 5, 2)
        >>> print(chunks)
        ['Hello', 'lo Wo', 'World', 'ld!']
    """
    if not text or chunk_size <= 0:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = min(start + chunk_size, text_length)

        # Extract chunk
        chunk = text[start:end]

        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)

        # Break if we've reached the end
        if end >= text_length:
            break

        # Move start position forward (with overlap)
        start += chunk_size - overlap

        # Prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            start = end

    return chunks


def clean_extracted_roles(roles_str: str) -> List[str]:
    """
    Cleans and parses roles extracted from LLM response.

    Handles various response formats:
    - Comma-separated values
    - Line-separated values
    - Bulleted lists
    - "None" responses

    Args:
        roles_str (str): Raw string from LLM containing roles

    Returns:
        List[str]: Clean list of unique role names

    Examples:
        >>> clean_extracted_roles("Engineer, Manager, Developer")
        ['Engineer', 'Manager', 'Developer']
        >>> clean_extracted_roles("None")
        []
    """
    if not roles_str or roles_str.strip().lower() == 'none':
        return []

    # Remove common list markers (bullets, numbers, dashes)
    roles_str = re.sub(r'^[\s\-•\*\d\.]+', '', roles_str, flags=re.MULTILINE)

    # Split by common delimiters (comma, semicolon, newline)
    roles = re.split(r'[,;\n]', roles_str)

    # Clean each role and remove empty entries
    cleaned_roles = []
    for role in roles:
        role = role.strip()
        if role and role.lower() != 'none':
            cleaned_roles.append(role)

    # Return unique roles while preserving order
    seen = set()
    unique_roles = []
    for role in cleaned_roles:
        if role.lower() not in seen:
            seen.add(role.lower())
            unique_roles.append(role)

    return unique_roles


def format_report_section(title: str, items: List[str], indent: int = 0) -> str:
    """
    Formats a section of the report with consistent styling.

    Args:
        title (str): Section title
        items (List[str]): List of items to display
        indent (int): Number of spaces to indent

    Returns:
        str: Formatted section text
    """
    indent_str = " " * indent
    result = f"\n{indent_str}--- {title} ---\n"

    if items:
        for item in items:
            result += f"{indent_str}- {item}\n"
    else:
        result += f"{indent_str}(None)\n"

    return result
