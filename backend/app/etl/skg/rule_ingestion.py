"""
Constructability Rule Ingestion Pipeline for the Strategic Knowledge Graph.

Supports ingestion from:
- JSON files (structured rule definitions)
- Code document parsing (IS 456, ACI 318, etc.)
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.skg.rule_models import (
    RuleCreate,
    RuleDiscipline,
    RuleImport,
    RuleImportRequest,
    RuleImportResult,
    RuleSeverity,
    RuleType,
)
from app.services.skg.rule_service import ConstructabilityRuleService

logger = logging.getLogger(__name__)


class RuleIngestion:
    """ETL pipeline for ingesting constructability rules into the Strategic Knowledge Graph."""

    # Common code references and their full names
    CODE_REFERENCES = {
        "IS 456": "IS 456:2000 - Plain and Reinforced Concrete - Code of Practice",
        "IS 800": "IS 800:2007 - General Construction in Steel - Code of Practice",
        "IS 1893": "IS 1893:2016 - Criteria for Earthquake Resistant Design of Structures",
        "IS 875": "IS 875 - Code of Practice for Design Loads",
        "ACI 318": "ACI 318 - Building Code Requirements for Structural Concrete",
        "AISC": "AISC 360 - Specification for Structural Steel Buildings",
        "IBC": "International Building Code",
    }

    def __init__(self, rule_service: Optional[ConstructabilityRuleService] = None):
        """
        Initialize the rule ingestion pipeline.

        Args:
            rule_service: Optional rule service instance
        """
        self.rule_service = rule_service or ConstructabilityRuleService()

    def ingest_from_json(
        self,
        file_path: str,
        created_by: str = "system",
        overwrite_existing: bool = False
    ) -> RuleImportResult:
        """
        Ingest rules from a JSON file.

        Expected JSON format:
        {
            "rules": [
                {
                    "rule_code": "IS456_REBAR_SPACING_MIN",
                    "rule_name": "Minimum Rebar Spacing",
                    "discipline": "structural",
                    "rule_type": "spacing_rule",
                    "source_code": "IS 456:2000",
                    "source_clause": "Clause 26.3.2",
                    "condition_expression": "$input.rebar_spacing < 25",
                    "condition_description": "Clear spacing between bars less than 25mm",
                    "recommendation": "Increase rebar spacing to minimum 25mm or maximum aggregate size + 5mm",
                    "severity": "critical",
                    "applicable_to": ["foundation_design", "beam_design"],
                    "is_mandatory": true
                }
            ]
        }

        Args:
            file_path: Path to JSON file
            created_by: User performing the import
            overwrite_existing: Whether to overwrite existing rules

        Returns:
            Import result with counts and errors
        """
        logger.info(f"Ingesting rules from JSON: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rules_data = data.get("rules", [])
        rules = []
        errors = []

        for idx, rule_data in enumerate(rules_data):
            try:
                rules.append(RuleImport(
                    rule_code=rule_data["rule_code"],
                    rule_name=rule_data["rule_name"],
                    description=rule_data.get("description"),
                    discipline=RuleDiscipline(rule_data["discipline"]),
                    rule_type=RuleType(rule_data["rule_type"]),
                    source_code=rule_data.get("source_code"),
                    source_clause=rule_data.get("source_clause"),
                    condition_expression=rule_data["condition_expression"],
                    condition_description=rule_data.get("condition_description"),
                    recommendation=rule_data["recommendation"],
                    severity=RuleSeverity(rule_data["severity"]),
                    applicable_to=rule_data.get("applicable_to", []),
                    is_mandatory=rule_data.get("is_mandatory", False)
                ))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "rule_code": rule_data.get("rule_code", "unknown"),
                    "error": str(e)
                })

        if rules:
            result = self.rule_service.import_rules(
                RuleImportRequest(
                    rules=rules,
                    overwrite_existing=overwrite_existing,
                    created_by=created_by
                )
            )
            result.errors.extend(errors)
            return result

        return RuleImportResult(
            total_rules=0,
            rules_created=0,
            rules_updated=0,
            rules_skipped=0,
            errors=errors
        )

    def create_standard_rules(
        self,
        created_by: str = "system"
    ) -> RuleImportResult:
        """
        Create a set of standard constructability rules based on common codes.

        This provides a baseline set of rules for IS 456, IS 800, etc.

        Args:
            created_by: User creating the rules

        Returns:
            Import result
        """
        logger.info("Creating standard constructability rules")

        rules = self._get_is456_rules() + self._get_is800_rules() + self._get_general_rules()

        return self.rule_service.import_rules(
            RuleImportRequest(
                rules=rules,
                overwrite_existing=False,
                created_by=created_by
            )
        )

    def _get_is456_rules(self) -> List[RuleImport]:
        """Get IS 456:2000 rules for RCC design."""
        return [
            # Minimum rebar spacing
            RuleImport(
                rule_code="IS456_REBAR_SPACING_MIN",
                rule_name="Minimum Reinforcement Spacing",
                description="Minimum clear spacing between parallel bars in RCC",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.SPACING_RULE,
                source_code="IS 456:2000",
                source_clause="Clause 26.3.2",
                condition_expression="$input.rebar_spacing < 25",
                condition_description="Clear spacing between bars is less than 25mm",
                recommendation="Minimum clear spacing should be: (a) 25mm, (b) diameter of larger bar, (c) 5mm more than nominal maximum size of coarse aggregate",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["foundation_design", "beam_design", "column_design", "slab_design"],
                is_mandatory=True
            ),
            # Maximum rebar spacing in slabs
            RuleImport(
                rule_code="IS456_SLAB_SPACING_MAX",
                rule_name="Maximum Slab Reinforcement Spacing",
                description="Maximum spacing of main reinforcement in slabs",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.SPACING_RULE,
                source_code="IS 456:2000",
                source_clause="Clause 26.3.3",
                condition_expression="$input.main_bar_spacing > 300",
                condition_description="Main reinforcement spacing exceeds 300mm",
                recommendation="Maximum spacing of main reinforcement in slabs should not exceed 3 times effective depth or 300mm, whichever is smaller",
                severity=RuleSeverity.HIGH,
                applicable_to=["slab_design"],
                is_mandatory=True
            ),
            # Minimum cover for foundations
            RuleImport(
                rule_code="IS456_FOUNDATION_COVER",
                rule_name="Minimum Cover for Foundations",
                description="Minimum clear cover for reinforcement in foundations",
                discipline=RuleDiscipline.CIVIL,
                rule_type=RuleType.CODE_PROVISION,
                source_code="IS 456:2000",
                source_clause="Clause 26.4.2.2",
                condition_expression="$input.clear_cover < 50",
                condition_description="Clear cover for foundation reinforcement is less than 50mm",
                recommendation="Minimum cover for footings should be 50mm when in contact with earth. Use 75mm for exposed faces",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["foundation_design"],
                is_mandatory=True
            ),
            # Minimum steel percentage
            RuleImport(
                rule_code="IS456_MIN_STEEL_PERCENT",
                rule_name="Minimum Steel Percentage",
                description="Minimum area of tension reinforcement",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.CODE_PROVISION,
                source_code="IS 456:2000",
                source_clause="Clause 26.5.1.1",
                condition_expression="$input.steel_percentage < 0.12",
                condition_description="Steel percentage is below minimum (0.12% for HYSD bars)",
                recommendation="Minimum reinforcement: 0.12% of gross area for Fe415/Fe500, 0.15% for Fe250",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["beam_design", "slab_design", "foundation_design"],
                is_mandatory=True
            ),
            # Formwork stripping time - beams
            RuleImport(
                rule_code="IS456_STRIPPING_BEAM",
                rule_name="Beam Formwork Stripping Time",
                description="Minimum time before removing beam/slab formwork",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.STRIPPING_TIME,
                source_code="IS 456:2000",
                source_clause="Clause 11.3.1",
                condition_expression="$input.stripping_days < 14",
                condition_description="Formwork removal planned before 14 days for beams spanning > 4.5m",
                recommendation="Props under beams spanning >4.5m should remain for minimum 14 days. For spans up to 4.5m, minimum 7 days",
                severity=RuleSeverity.HIGH,
                applicable_to=["beam_design"],
                is_mandatory=False
            ),
            # Concrete grade minimum
            RuleImport(
                rule_code="IS456_CONCRETE_GRADE_MIN",
                rule_name="Minimum Concrete Grade for RCC",
                description="Minimum grade of concrete for reinforced concrete work",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.CODE_PROVISION,
                source_code="IS 456:2000",
                source_clause="Clause 6.1.1",
                condition_expression="$input.concrete_grade_value < 20",
                condition_description="Concrete grade below M20 for RCC work",
                recommendation="Minimum grade of concrete for RCC shall be M20. Use M25 for moderate exposure, M30 for severe exposure",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["foundation_design", "beam_design", "column_design", "slab_design"],
                is_mandatory=True
            ),
        ]

    def _get_is800_rules(self) -> List[RuleImport]:
        """Get IS 800:2007 rules for steel design."""
        return [
            # Minimum thickness for corrosion protection
            RuleImport(
                rule_code="IS800_MIN_THICKNESS",
                rule_name="Minimum Steel Member Thickness",
                description="Minimum thickness of steel members for durability",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.CODE_PROVISION,
                source_code="IS 800:2007",
                source_clause="Clause 3.7.4",
                condition_expression="$input.member_thickness < 6",
                condition_description="Steel member thickness less than 6mm",
                recommendation="Minimum thickness should be 6mm for members exposed to weather and 4mm for protected members. Consider corrosion allowance for aggressive environments",
                severity=RuleSeverity.HIGH,
                applicable_to=["steel_column_design", "steel_beam_design"],
                is_mandatory=False
            ),
            # Slenderness ratio limit
            RuleImport(
                rule_code="IS800_SLENDERNESS_LIMIT",
                rule_name="Slenderness Ratio Limit",
                description="Maximum slenderness ratio for compression members",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.CODE_PROVISION,
                source_code="IS 800:2007",
                source_clause="Clause 3.8.1",
                condition_expression="$input.slenderness_ratio > 180",
                condition_description="Slenderness ratio exceeds 180 for compression member",
                recommendation="Maximum slenderness ratio: 180 for columns, 250 for struts carrying wind/earthquake loads only, 350 for tension members",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["steel_column_design"],
                is_mandatory=True
            ),
            # Bolt edge distance
            RuleImport(
                rule_code="IS800_BOLT_EDGE_DIST",
                rule_name="Bolt Edge Distance",
                description="Minimum edge distance for bolted connections",
                discipline=RuleDiscipline.STRUCTURAL,
                rule_type=RuleType.SPACING_RULE,
                source_code="IS 800:2007",
                source_clause="Clause 10.2.4.2",
                condition_expression="$input.edge_distance < $input.bolt_diameter * 1.5",
                condition_description="Edge distance less than 1.5 times bolt hole diameter",
                recommendation="Minimum edge distance should be 1.5 times bolt hole diameter for sheared edges, 1.2 times for rolled/machine-cut edges",
                severity=RuleSeverity.HIGH,
                applicable_to=["steel_column_design", "steel_beam_design"],
                is_mandatory=True
            ),
        ]

    def _get_general_rules(self) -> List[RuleImport]:
        """Get general best practice rules."""
        return [
            # Foundation depth check
            RuleImport(
                rule_code="GEN_FOUNDATION_DEPTH",
                rule_name="Minimum Foundation Depth",
                description="Minimum depth of foundation below ground level",
                discipline=RuleDiscipline.CIVIL,
                rule_type=RuleType.BEST_PRACTICE,
                source_code=None,
                source_clause=None,
                condition_expression="$input.foundation_depth < 0.5",
                condition_description="Foundation depth less than 0.5m below ground",
                recommendation="Foundation should be minimum 0.5m below natural ground level. In frost-prone areas, place below frost line. In expansive soils, go below zone of seasonal moisture variation",
                severity=RuleSeverity.MEDIUM,
                applicable_to=["foundation_design"],
                is_mandatory=False
            ),
            # High load warning
            RuleImport(
                rule_code="GEN_HIGH_LOAD_WARNING",
                rule_name="High Load Warning",
                description="Warning for unusually high loads",
                discipline=RuleDiscipline.GENERAL,
                rule_type=RuleType.QUALITY_CHECK,
                source_code=None,
                source_clause=None,
                condition_expression="$input.total_load > 5000",
                condition_description="Total load exceeds 5000 kN",
                recommendation="High load detected. Verify load calculations and consider pile foundation or combined footing. Check for load path optimization",
                severity=RuleSeverity.INFO,
                applicable_to=["foundation_design", "column_design"],
                is_mandatory=False
            ),
            # Low SBC warning
            RuleImport(
                rule_code="GEN_LOW_SBC_WARNING",
                rule_name="Low Bearing Capacity Warning",
                description="Warning for low safe bearing capacity",
                discipline=RuleDiscipline.CIVIL,
                rule_type=RuleType.QUALITY_CHECK,
                source_code=None,
                source_clause=None,
                condition_expression="$input.safe_bearing_capacity < 100",
                condition_description="Safe bearing capacity below 100 kN/m²",
                recommendation="Low SBC detected. Consider soil improvement, pile foundation, or raft foundation. Verify with geotechnical report",
                severity=RuleSeverity.HIGH,
                applicable_to=["foundation_design"],
                is_mandatory=False
            ),
            # Safety check for excavation depth
            RuleImport(
                rule_code="SAFETY_EXCAVATION_DEPTH",
                rule_name="Deep Excavation Safety",
                description="Safety requirements for deep excavations",
                discipline=RuleDiscipline.CIVIL,
                rule_type=RuleType.SAFETY_REQUIREMENT,
                source_code=None,
                source_clause=None,
                condition_expression="$input.excavation_depth > 1.5",
                condition_description="Excavation depth exceeds 1.5m",
                recommendation="Deep excavation requires: (1) Shoring/sheet piling, (2) Safety barriers, (3) Access ladders every 15m, (4) Daily inspection, (5) Dewatering plan if water table is high",
                severity=RuleSeverity.CRITICAL,
                applicable_to=["foundation_design"],
                is_mandatory=True
            ),
        ]

    def parse_code_document(
        self,
        file_path: str,
        source_code: str,
        discipline: RuleDiscipline,
        created_by: str = "system"
    ) -> RuleImportResult:
        """
        Parse a code document (PDF/TXT) to extract rules.

        This is a basic implementation that looks for common patterns.
        For production use, consider using LLM-based extraction.

        Args:
            file_path: Path to the document
            source_code: Code reference (e.g., "IS 456:2000")
            discipline: Engineering discipline
            created_by: User performing the import

        Returns:
            Import result
        """
        logger.info(f"Parsing code document: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Read document content
        if path.suffix.lower() == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            logger.warning(f"Unsupported file type: {path.suffix}. Use .txt files")
            return RuleImportResult(
                total_rules=0,
                rules_created=0,
                rules_updated=0,
                rules_skipped=0,
                errors=[{"error": f"Unsupported file type: {path.suffix}"}]
            )

        # Extract rules using pattern matching
        rules = self._extract_rules_from_text(content, source_code, discipline)

        if rules:
            return self.rule_service.import_rules(
                RuleImportRequest(
                    rules=rules,
                    overwrite_existing=False,
                    created_by=created_by
                )
            )

        return RuleImportResult(
            total_rules=0,
            rules_created=0,
            rules_updated=0,
            rules_skipped=0,
            errors=[]
        )

    def _extract_rules_from_text(
        self,
        content: str,
        source_code: str,
        discipline: RuleDiscipline
    ) -> List[RuleImport]:
        """Extract rules from text content using pattern matching."""
        rules = []

        # Pattern for clauses with "shall" requirements
        clause_pattern = r'(?:Clause|Section)\s*(\d+(?:\.\d+)*)[:\s]+([^.]+shall[^.]+\.)'
        matches = re.findall(clause_pattern, content, re.IGNORECASE)

        for idx, (clause_num, text) in enumerate(matches[:20]):  # Limit to 20 rules
            # Generate rule code
            code_prefix = source_code.replace(" ", "").replace(":", "_").upper()
            rule_code = f"{code_prefix}_RULE_{idx+1}"

            # Determine rule type and severity from text
            rule_type, severity = self._classify_rule_text(text)

            rules.append(RuleImport(
                rule_code=rule_code,
                rule_name=f"Clause {clause_num} Requirement",
                description=text[:500],
                discipline=discipline,
                rule_type=rule_type,
                source_code=source_code,
                source_clause=f"Clause {clause_num}",
                condition_expression="true",  # Manual review needed
                condition_description="Extracted from code - requires manual condition setup",
                recommendation=text[:1000],
                severity=severity,
                applicable_to=[],
                is_mandatory="shall" in text.lower()
            ))

        logger.info(f"Extracted {len(rules)} rules from document")
        return rules

    def _classify_rule_text(self, text: str) -> tuple[RuleType, RuleSeverity]:
        """Classify rule type and severity from text."""
        text_lower = text.lower()

        # Determine rule type
        if any(word in text_lower for word in ["spacing", "distance", "clearance"]):
            rule_type = RuleType.SPACING_RULE
        elif any(word in text_lower for word in ["safety", "hazard", "protect"]):
            rule_type = RuleType.SAFETY_REQUIREMENT
        elif any(word in text_lower for word in ["check", "verify", "inspect"]):
            rule_type = RuleType.QUALITY_CHECK
        elif any(word in text_lower for word in ["remove", "strip", "time"]):
            rule_type = RuleType.STRIPPING_TIME
        else:
            rule_type = RuleType.CODE_PROVISION

        # Determine severity
        if "shall not" in text_lower or "must" in text_lower:
            severity = RuleSeverity.CRITICAL
        elif "shall" in text_lower:
            severity = RuleSeverity.HIGH
        elif "should" in text_lower:
            severity = RuleSeverity.MEDIUM
        else:
            severity = RuleSeverity.LOW

        return rule_type, severity
