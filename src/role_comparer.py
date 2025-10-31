# src/role_comparer.py
"""
Role comparison module with fuzzy matching capabilities.
Compares XML-defined roles against PDF-extracted roles.
"""

from typing import List, Tuple, Dict, Set, Any
from src.utils import normalize_role, fuzzy_match, fuzzy_partial_match
from config.config import FUZZY_MATCH_THRESHOLD


class RoleComparer:
    """
    Compares job roles from XML and PDF with intelligent matching.

    Features:
    - Exact matching (normalized)
    - Fuzzy matching for typos and variations
    - Partial matching for abbreviations
    - Detailed reporting
    """

    def __init__(self, fuzzy_threshold: int = FUZZY_MATCH_THRESHOLD):
        """
        Initialize role comparer with fuzzy matching threshold.

        Args:
            fuzzy_threshold (int): Minimum similarity score (0-100) for fuzzy matches
        """
        self.fuzzy_threshold = fuzzy_threshold
        print(
            f"✅ Role Comparer initialized with fuzzy threshold: {fuzzy_threshold}")

    def compare_roles(
        self,
        xml_roles: List[str],
        pdf_roles: List[str]
    ) -> Tuple[bool, List[str], List[str], Dict[str, str]]:
        """
        Compares roles from XML and PDF to identify matches and discrepancies.

        Matching Strategy:
        1. Direct matching (after normalization)
        2. Fuzzy matching (for typos like "Managar" vs "Manager")
        3. Partial matching (for abbreviations like "SW Eng" vs "Software Engineer")

        Args:
            xml_roles (List[str]): List of roles from XML (ground truth)
            pdf_roles (List[str]): List of roles extracted from PDF

        Returns:
            Tuple containing:
            - is_incorrect (bool): True if there are unmatched PDF roles
            - matched_roles (List[str]): Roles that matched (using XML names)
            - incorrect_pdf_roles (List[str]): PDF roles with no match
            - fuzzy_matches (Dict[str, str]): Mapping of PDF role -> XML role for fuzzy matches
        """
        print("\n⚖️  Comparing XML roles vs PDF roles...")

        # Normalize XML roles for comparison
        normalized_xml_roles: Dict[str, str] = {
            normalize_role(role): role for role in xml_roles
        }

        # Normalize PDF roles and keep mapping to originals
        normalized_pdf_to_original: Dict[str, str] = {
            normalize_role(role): role for role in pdf_roles
        }

        # Track matched roles and fuzzy matches
        matched_xml_roles: Set[str] = set()
        fuzzy_match_map: Dict[str, str] = {}  # PDF role -> XML role
        potentially_incorrect: Set[str] = set(
            normalized_pdf_to_original.keys())

        # Step 1: Direct (exact) matching after normalization
        print("🔍 Step 1: Direct matching...")
        for norm_pdf, orig_pdf in normalized_pdf_to_original.items():
            if norm_pdf in normalized_xml_roles:
                # Exact match found
                matched_xml_roles.add(normalized_xml_roles[norm_pdf])
                potentially_incorrect.discard(norm_pdf)
                print(
                    f"  ✓ Direct match: '{orig_pdf}' = '{normalized_xml_roles[norm_pdf]}'")

        # Step 2: Fuzzy matching for remaining PDF roles
        if potentially_incorrect:
            print(
                f"\n🔍 Step 2: Fuzzy matching for {len(potentially_incorrect)} unmatched roles...")

            still_incorrect: Set[str] = set()

            for norm_pdf in potentially_incorrect:
                orig_pdf = normalized_pdf_to_original[norm_pdf]
                found_match = False

                # Try fuzzy matching against all XML roles
                for orig_xml in xml_roles:
                    # Try full fuzzy match
                    if fuzzy_match(orig_pdf, orig_xml, self.fuzzy_threshold):
                        matched_xml_roles.add(orig_xml)
                        fuzzy_match_map[orig_pdf] = orig_xml
                        found_match = True
                        print(f"  ≈ Fuzzy match: '{orig_pdf}' ≈ '{orig_xml}'")
                        break

                    # Try partial match (good for abbreviations)
                    if fuzzy_partial_match(orig_pdf, orig_xml, self.fuzzy_threshold):
                        matched_xml_roles.add(orig_xml)
                        fuzzy_match_map[orig_pdf] = orig_xml
                        found_match = True
                        print(
                            f"  ≈ Partial match: '{orig_pdf}' ≈ '{orig_xml}'")
                        break

                if not found_match:
                    still_incorrect.add(norm_pdf)
        else:
            still_incorrect = set()

        # Determine if PDF has incorrect roles
        is_incorrect = bool(still_incorrect)

        # Prepare final results
        final_matched_roles = sorted(list(matched_xml_roles))
        final_incorrect_roles = sorted([
            normalized_pdf_to_original[norm] for norm in still_incorrect
        ])

        # Log summary
        print(f"\n📊 Comparison Summary:")
        print(f"  • XML Roles: {len(xml_roles)}")
        print(f"  • PDF Roles: {len(pdf_roles)}")
        print(f"  • Matched: {len(final_matched_roles)}")
        print(f"  • Fuzzy Matched: {len(fuzzy_match_map)}")
        print(f"  • Incorrect: {len(final_incorrect_roles)}")

        return (
            is_incorrect,
            final_matched_roles,
            final_incorrect_roles,
            fuzzy_match_map
        )

    def generate_report(
        self,
        is_incorrect: bool,
        matched_roles: List[str],
        incorrect_pdf_roles: List[str],
        fuzzy_matches: Dict[str, str],
        xml_roles: List[str],
        pdf_roles: List[str]
    ) -> str:
        """
        Generates a detailed comparison report.

        Args:
            is_incorrect (bool): Whether PDF has incorrect roles
            matched_roles (List[str]): Successfully matched roles
            incorrect_pdf_roles (List[str]): Unmatched PDF roles
            fuzzy_matches (Dict[str, str]): Fuzzy match mappings
            xml_roles (List[str]): Original XML roles
            pdf_roles (List[str]): Original PDF roles

        Returns:
            str: Formatted report text
        """
        report_lines = []

        # Header
        report_lines.append("\n" + "=" * 60)
        report_lines.append("       📋 ROLE VALIDATION REPORT")
        report_lines.append("=" * 60)

        # Statistics
        report_lines.append("\n📊 STATISTICS:")
        report_lines.append(
            f"  • Total Unique Roles in XML: {len(set(xml_roles))}")
        report_lines.append(
            f"  • Total Unique Roles in PDF: {len(set(pdf_roles))}")
        report_lines.append(f"  • Successfully Matched: {len(matched_roles)}")
        report_lines.append(f"  • Fuzzy Matched: {len(fuzzy_matches)}")
        report_lines.append(
            f"  • Incorrect/Unmatched: {len(incorrect_pdf_roles)}")

        # Matched Roles Section
        report_lines.append("\n✅ MATCHED ROLES (XML ↔ PDF):")
        if matched_roles:
            for role in matched_roles:
                # Check if it was a fuzzy match
                fuzzy_pdf_role = None
                for pdf_role, xml_role in fuzzy_matches.items():
                    if xml_role == role:
                        fuzzy_pdf_role = pdf_role
                        break

                if fuzzy_pdf_role:
                    report_lines.append(
                        f"  ≈ {role} (fuzzy matched: '{fuzzy_pdf_role}')")
                else:
                    report_lines.append(f"  ✓ {role}")
        else:
            report_lines.append("  (No matches found)")

        # Incorrect Roles Section
        report_lines.append("\n❌ INCORRECT PDF ROLES (Not in XML):")
        if incorrect_pdf_roles:
            for role in incorrect_pdf_roles:
                report_lines.append(f"  ✗ {role}")
        else:
            report_lines.append("  (None - All PDF roles matched XML)")

        # Missing Roles (in XML but not found in PDF)
        pdf_matched_set = set([r.lower() for r in matched_roles])
        missing_roles = [r for r in xml_roles if r.lower()
                         not in pdf_matched_set]

        if missing_roles:
            report_lines.append("\n⚠️  ROLES IN XML BUT NOT FOUND IN PDF:")
            for role in missing_roles:
                report_lines.append(f"  ⊘ {role}")

        # Conclusion
        report_lines.append("\n" + "=" * 60)
        if is_incorrect:
            report_lines.append("🔴 CONCLUSION: PDF CONTAINS INCORRECT ROLES")
            report_lines.append(
                "   → Some roles in the PDF do not match XML definitions")
        else:
            report_lines.append("🟢 CONCLUSION: ALL PDF ROLES ARE CORRECT")
            report_lines.append("   → All roles in PDF match XML definitions")
        report_lines.append("=" * 60 + "\n")

        return "\n".join(report_lines)

    def print_report(
        self,
        is_incorrect: bool,
        matched_roles: List[str],
        incorrect_pdf_roles: List[str],
        fuzzy_matches: Dict[str, str],
        xml_roles: List[str],
        pdf_roles: List[str]
    ):
        """
        Prints the comparison report to console.

        Args:
            Same as generate_report()
        """
        report = self.generate_report(
            is_incorrect,
            matched_roles,
            incorrect_pdf_roles,
            fuzzy_matches,
            xml_roles,
            pdf_roles
        )
        print(report)

    def get_match_statistics(
        self,
        matched_roles: List[str],
        incorrect_pdf_roles: List[str],
        xml_roles: List[str],
        pdf_roles: List[str]
    ) -> Dict[str, Any]:
        """
        Returns match statistics as a dictionary.

        Useful for programmatic access or JSON export.

        Args:
            matched_roles (List[str]): Matched roles
            incorrect_pdf_roles (List[str]): Incorrect PDF roles
            xml_roles (List[str]): Original XML roles
            pdf_roles (List[str]): Original PDF roles

        Returns:
            Dict: Statistics dictionary
        """
        total_xml = len(set(xml_roles))
        total_pdf = len(set(pdf_roles))
        total_matched = len(matched_roles)
        total_incorrect = len(incorrect_pdf_roles)

        match_rate = (total_matched / total_pdf * 100) if total_pdf > 0 else 0

        return {
            "total_xml_roles": total_xml,
            "total_pdf_roles": total_pdf,
            "matched_count": total_matched,
            "incorrect_count": total_incorrect,
            "match_rate_percentage": round(match_rate, 2),
            "is_valid": total_incorrect == 0,
            "matched_roles": matched_roles,
            "incorrect_roles": incorrect_pdf_roles
        }
