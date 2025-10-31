# src/xml_parser.py
"""
XML parser module for extracting job roles.
Uses lxml for efficient XPath-based extraction.
"""

import os
from typing import List
from lxml import etree  # type:ignore


def extract_roles_from_xml(xml_filepath: str, role_xpath: str) -> List[str]:
    """
    Extracts role names from an XML file using XPath.

    This function parses an XML file and extracts text content
    from elements matching the specified XPath expression.

    Args:
        xml_filepath (str): Path to the XML file
        role_xpath (str): XPath expression to locate role elements
                         (e.g., '//role/text()' for <role>Software Engineer</role>)

    Returns:
        List[str]: List of extracted role names

    Examples:
        >>> roles = extract_roles_from_xml('roles.xml', '//role/text()')
        >>> print(roles)
        ['Software Engineer', 'Project Manager', 'Data Scientist']
    """
    # Validate file existence
    if not os.path.exists(xml_filepath):
        print(f"❌ Error: XML file not found at {xml_filepath}")
        return []

    try:
        # Create parser with UTF-8 encoding and recovery mode
        # Recovery mode helps handle minor XML formatting issues
        parser = etree.XMLParser(recover=True, encoding='utf-8')

        # Parse the XML file
        tree = etree.parse(xml_filepath, parser=parser)

        # Apply XPath to extract role text
        role_elements = tree.xpath(role_xpath)

        # Convert to strings and clean up
        roles = []
        for element in role_elements:
            if element is not None:
                # Convert to string and strip whitespace
                role_text = str(element).strip()
                if role_text:  # Only add non-empty roles
                    roles.append(role_text)

        print(f"✅ Extracted {len(roles)} roles from XML")

        # Log extracted roles for debugging
        if roles:
            print(f"📋 XML Roles: {', '.join(roles[:5])}" +
                  (f" ... and {len(roles) - 5} more" if len(roles) > 5 else ""))

        return roles

    except etree.XMLSyntaxError as e:
        print(f"❌ XML Syntax Error in file {xml_filepath}: {e}")
        print("   Please ensure your XML file is properly formatted.")
        return []

    except Exception as e:
        print(f"❌ Unexpected error while parsing XML: {e}")
        return []


def validate_xml_structure(xml_filepath: str) -> bool:
    """
    Validates that an XML file is well-formed.

    Args:
        xml_filepath (str): Path to the XML file

    Returns:
        bool: True if XML is valid, False otherwise
    """
    if not os.path.exists(xml_filepath):
        print(f"❌ Error: XML file not found at {xml_filepath}")
        return False

    try:
        parser = etree.XMLParser(encoding='utf-8')
        etree.parse(xml_filepath, parser=parser)
        print(f"✅ XML file is well-formed: {xml_filepath}")
        return True

    except etree.XMLSyntaxError as e:
        print(f"❌ XML validation failed: {e}")
        return False

    except Exception as e:
        print(f"❌ Error validating XML: {e}")
        return False


def extract_roles_with_attributes(
    xml_filepath: str,
    role_xpath: str,
    attributes: List[str]
) -> List[dict]:
    """
    Extracts roles along with their XML attributes.

    Useful if your XML contains additional metadata like:
    <role level="senior" department="engineering">Software Engineer</role>

    Args:
        xml_filepath (str): Path to the XML file
        role_xpath (str): XPath to locate role elements (not text())
        attributes (List[str]): List of attribute names to extract

    Returns:
        List[dict]: List of dictionaries containing role and attributes
    """
    if not os.path.exists(xml_filepath):
        print(f"❌ Error: XML file not found at {xml_filepath}")
        return []

    try:
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.parse(xml_filepath, parser=parser)

        # Get role elements (not text nodes)
        role_elements = tree.xpath(role_xpath)

        roles_with_attrs = []
        for element in role_elements:
            if element is not None:
                role_data = {
                    'name': element.text.strip() if element.text else ""
                }

                # Extract requested attributes
                if attributes:
                    for attr in attributes:
                        role_data[attr] = element.get(attr, "")

                if role_data['name']:  # Only add if name is not empty
                    roles_with_attrs.append(role_data)

        print(f"✅ Extracted {len(roles_with_attrs)} roles with attributes")

        return roles_with_attrs

    except Exception as e:
        print(f"❌ Error extracting roles with attributes: {e}")
        return []


def get_xml_statistics(xml_filepath: str, role_xpath: str) -> dict:
    """
    Returns statistics about the XML file.

    Args:
        xml_filepath (str): Path to the XML file
        role_xpath (str): XPath expression for roles

    Returns:
        dict: Dictionary containing XML statistics
    """
    if not os.path.exists(xml_filepath):
        return {"error": "File not found"}

    try:
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.parse(xml_filepath, parser=parser)
        root = tree.getroot()

        roles = tree.xpath(role_xpath)

        stats = {
            "root_tag": root.tag,
            "total_elements": len(list(root.iter())),
            "total_roles": len(roles),
            "file_size_bytes": os.path.getsize(xml_filepath),
            "file_path": xml_filepath
        }

        return stats

    except Exception as e:
        return {"error": str(e)}
