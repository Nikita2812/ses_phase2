"""
Lessons Learned Ingestion Pipeline for the Strategic Knowledge Graph.

Supports ingestion from:
- JSON files (structured lesson data)
- CSV files (tabular lesson data)
- Project closeout reports (text extraction)
"""

import csv
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.skg.lesson_models import (
    IssueCategory,
    LessonCreate,
    LessonDiscipline,
    LessonImport,
    LessonImportRequest,
    LessonImportResult,
    LessonSeverity,
)
from app.services.skg.lesson_service import LessonsLearnedService

logger = logging.getLogger(__name__)


class LessonIngestion:
    """ETL pipeline for ingesting lessons learned into the Strategic Knowledge Graph."""

    # Column mappings for CSV import
    COLUMN_MAPPINGS = {
        "lesson_code": ["lesson_code", "code", "id", "lesson_id"],
        "title": ["title", "name", "lesson_title", "subject"],
        "project_name": ["project_name", "project", "project_title"],
        "discipline": ["discipline", "dept", "department"],
        "issue_category": ["issue_category", "category", "issue_type", "type"],
        "issue_description": ["issue_description", "issue", "description", "problem"],
        "root_cause": ["root_cause", "cause", "reason", "why"],
        "solution": ["solution", "resolution", "action_taken", "corrective_action"],
        "preventive_measures": ["preventive_measures", "prevention", "preventive_action"],
        "cost_impact": ["cost_impact", "cost", "financial_impact", "amount"],
        "schedule_impact_days": ["schedule_impact_days", "schedule_impact", "days_delay", "delay"],
        "severity": ["severity", "priority", "level", "importance"],
        "tags": ["tags", "keywords", "labels"],
        "source": ["source", "reference", "origin"],
    }

    # Category normalization
    CATEGORY_MAPPINGS = {
        "safety": IssueCategory.SAFETY,
        "accident": IssueCategory.SAFETY,
        "injury": IssueCategory.SAFETY,
        "cost": IssueCategory.COST_OVERRUN,
        "budget": IssueCategory.COST_OVERRUN,
        "overrun": IssueCategory.COST_OVERRUN,
        "over budget": IssueCategory.COST_OVERRUN,
        "schedule": IssueCategory.SCHEDULE_DELAY,
        "delay": IssueCategory.SCHEDULE_DELAY,
        "late": IssueCategory.SCHEDULE_DELAY,
        "time": IssueCategory.SCHEDULE_DELAY,
        "quality": IssueCategory.QUALITY_DEFECT,
        "defect": IssueCategory.QUALITY_DEFECT,
        "rework": IssueCategory.QUALITY_DEFECT,
        "design": IssueCategory.DESIGN_ERROR,
        "error": IssueCategory.DESIGN_ERROR,
        "mistake": IssueCategory.DESIGN_ERROR,
        "coordination": IssueCategory.COORDINATION_ISSUE,
        "communication": IssueCategory.COORDINATION_ISSUE,
        "material": IssueCategory.MATERIAL_ISSUE,
        "supply": IssueCategory.MATERIAL_ISSUE,
        "procurement": IssueCategory.MATERIAL_ISSUE,
        "execution": IssueCategory.EXECUTION_ISSUE,
        "construction": IssueCategory.EXECUTION_ISSUE,
        "site": IssueCategory.EXECUTION_ISSUE,
    }

    # Discipline normalization
    DISCIPLINE_MAPPINGS = {
        "civil": LessonDiscipline.CIVIL,
        "foundation": LessonDiscipline.CIVIL,
        "earthwork": LessonDiscipline.CIVIL,
        "structural": LessonDiscipline.STRUCTURAL,
        "structure": LessonDiscipline.STRUCTURAL,
        "rcc": LessonDiscipline.STRUCTURAL,
        "steel": LessonDiscipline.STRUCTURAL,
        "architectural": LessonDiscipline.ARCHITECTURAL,
        "architecture": LessonDiscipline.ARCHITECTURAL,
        "finishing": LessonDiscipline.ARCHITECTURAL,
        "mep": LessonDiscipline.MEP,
        "mechanical": LessonDiscipline.MEP,
        "electrical": LessonDiscipline.MEP,
        "plumbing": LessonDiscipline.MEP,
    }

    # Severity normalization
    SEVERITY_MAPPINGS = {
        "critical": LessonSeverity.CRITICAL,
        "very high": LessonSeverity.CRITICAL,
        "severe": LessonSeverity.CRITICAL,
        "high": LessonSeverity.HIGH,
        "major": LessonSeverity.HIGH,
        "significant": LessonSeverity.HIGH,
        "medium": LessonSeverity.MEDIUM,
        "moderate": LessonSeverity.MEDIUM,
        "low": LessonSeverity.LOW,
        "minor": LessonSeverity.LOW,
    }

    def __init__(self, lesson_service: Optional[LessonsLearnedService] = None):
        """
        Initialize the lesson ingestion pipeline.

        Args:
            lesson_service: Optional lesson service instance
        """
        self.lesson_service = lesson_service or LessonsLearnedService()

    def ingest_from_json(
        self,
        file_path: str,
        reported_by: str = "system",
        overwrite_existing: bool = False
    ) -> LessonImportResult:
        """
        Ingest lessons from a JSON file.

        Expected JSON format:
        {
            "lessons": [
                {
                    "lesson_code": "LL-2024-001",
                    "title": "Foundation Settlement Issue",
                    "project_name": "ABC Project",
                    "discipline": "civil",
                    "issue_category": "quality_defect",
                    "issue_description": "Settlement observed in foundation...",
                    "root_cause": "Inadequate compaction of backfill...",
                    "solution": "Re-excavated and re-compacted...",
                    "preventive_measures": ["Ensure proper compaction testing", "..."],
                    "cost_impact": 150000,
                    "schedule_impact_days": 14,
                    "severity": "high",
                    "tags": ["foundation", "settlement", "backfill"]
                }
            ]
        }

        Args:
            file_path: Path to JSON file
            reported_by: User performing the import
            overwrite_existing: Whether to overwrite existing lessons

        Returns:
            Import result with counts and errors
        """
        logger.info(f"Ingesting lessons from JSON: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lessons_data = data.get("lessons", [])
        lessons = []
        errors = []

        for idx, lesson_data in enumerate(lessons_data):
            try:
                lessons.append(LessonImport(
                    lesson_code=lesson_data["lesson_code"],
                    title=lesson_data["title"],
                    project_name=lesson_data.get("project_name"),
                    discipline=LessonDiscipline(lesson_data["discipline"]),
                    deliverable_type=lesson_data.get("deliverable_type"),
                    issue_category=IssueCategory(lesson_data["issue_category"]),
                    issue_description=lesson_data["issue_description"],
                    root_cause=lesson_data["root_cause"],
                    solution=lesson_data["solution"],
                    preventive_measures=lesson_data.get("preventive_measures", []),
                    cost_impact=Decimal(str(lesson_data["cost_impact"])) if lesson_data.get("cost_impact") else None,
                    schedule_impact_days=lesson_data.get("schedule_impact_days"),
                    severity=LessonSeverity(lesson_data["severity"]),
                    tags=lesson_data.get("tags", []),
                    applicable_to=lesson_data.get("applicable_to", []),
                    source=lesson_data.get("source")
                ))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "lesson_code": lesson_data.get("lesson_code", "unknown"),
                    "error": str(e)
                })

        if lessons:
            result = self.lesson_service.import_lessons(
                LessonImportRequest(
                    lessons=lessons,
                    overwrite_existing=overwrite_existing,
                    reported_by=reported_by
                )
            )
            result.errors.extend(errors)
            return result

        return LessonImportResult(
            total_lessons=0,
            lessons_created=0,
            lessons_updated=0,
            lessons_skipped=0,
            errors=errors
        )

    def ingest_from_csv(
        self,
        file_path: str,
        reported_by: str = "system",
        overwrite_existing: bool = False
    ) -> LessonImportResult:
        """
        Ingest lessons from a CSV file.

        Args:
            file_path: Path to CSV file
            reported_by: User performing the import
            overwrite_existing: Whether to overwrite existing lessons

        Returns:
            Import result with counts and errors
        """
        logger.info(f"Ingesting lessons from CSV: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        with open(path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        return self._process_csv_content(content, reported_by, overwrite_existing)

    def _process_csv_content(
        self,
        content: str,
        reported_by: str,
        overwrite_existing: bool
    ) -> LessonImportResult:
        """Process CSV content and import lessons."""
        reader = csv.DictReader(StringIO(content))
        headers = reader.fieldnames or []

        column_map = self._map_columns(headers)
        lessons = []
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                lesson = self._parse_csv_row(row, column_map, row_num)
                if lesson:
                    lessons.append(lesson)
            except Exception as e:
                errors.append({
                    "row": row_num,
                    "error": str(e)
                })
                logger.warning(f"Failed to parse row {row_num}: {e}")

        logger.info(f"Parsed {len(lessons)} lessons from CSV")

        if lessons:
            result = self.lesson_service.import_lessons(
                LessonImportRequest(
                    lessons=lessons,
                    overwrite_existing=overwrite_existing,
                    reported_by=reported_by
                )
            )
            result.errors.extend(errors)
            return result

        return LessonImportResult(
            total_lessons=0,
            lessons_created=0,
            lessons_updated=0,
            lessons_skipped=0,
            errors=errors
        )

    def _map_columns(self, headers: List[str]) -> Dict[str, str]:
        """Map CSV column headers to schema fields."""
        column_map = {}
        headers_lower = [h.lower().strip() for h in headers]

        for field, aliases in self.COLUMN_MAPPINGS.items():
            for alias in aliases:
                if alias in headers_lower:
                    idx = headers_lower.index(alias)
                    column_map[field] = headers[idx]
                    break

        return column_map

    def _parse_csv_row(
        self,
        row: Dict[str, str],
        column_map: Dict[str, str],
        row_num: int
    ) -> Optional[LessonImport]:
        """Parse a CSV row into a LessonImport."""
        # Required fields
        lesson_code = self._get_field(row, column_map, "lesson_code")
        title = self._get_field(row, column_map, "title")
        issue_description = self._get_field(row, column_map, "issue_description")
        root_cause = self._get_field(row, column_map, "root_cause")
        solution = self._get_field(row, column_map, "solution")

        if not all([lesson_code, title, issue_description, root_cause, solution]):
            raise ValueError("Missing required fields")

        # Parse category
        category_str = self._get_field(row, column_map, "issue_category") or ""
        category = self._normalize_category(category_str, issue_description)

        # Parse discipline
        discipline_str = self._get_field(row, column_map, "discipline") or ""
        discipline = self._normalize_discipline(discipline_str, issue_description)

        # Parse severity
        severity_str = self._get_field(row, column_map, "severity") or ""
        severity = self._normalize_severity(severity_str)

        # Parse optional fields
        cost_impact = None
        cost_str = self._get_field(row, column_map, "cost_impact")
        if cost_str:
            try:
                cost_impact = Decimal(cost_str.replace(",", "").strip())
            except InvalidOperation:
                pass

        schedule_impact = None
        schedule_str = self._get_field(row, column_map, "schedule_impact_days")
        if schedule_str:
            try:
                schedule_impact = int(schedule_str.strip())
            except ValueError:
                pass

        # Parse tags
        tags_str = self._get_field(row, column_map, "tags") or ""
        tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]

        # Parse preventive measures
        measures_str = self._get_field(row, column_map, "preventive_measures") or ""
        preventive_measures = [m.strip() for m in measures_str.split(";") if m.strip()]

        return LessonImport(
            lesson_code=lesson_code.strip(),
            title=title.strip(),
            project_name=self._get_field(row, column_map, "project_name"),
            discipline=discipline,
            issue_category=category,
            issue_description=issue_description.strip(),
            root_cause=root_cause.strip(),
            solution=solution.strip(),
            preventive_measures=preventive_measures,
            cost_impact=cost_impact,
            schedule_impact_days=schedule_impact,
            severity=severity,
            tags=tags,
            source=self._get_field(row, column_map, "source")
        )

    def _get_field(
        self,
        row: Dict[str, str],
        column_map: Dict[str, str],
        field: str
    ) -> Optional[str]:
        """Get a field value from a CSV row."""
        column = column_map.get(field)
        if column and column in row:
            value = row[column].strip()
            return value if value else None
        return None

    def _normalize_category(self, category_str: str, description: str) -> IssueCategory:
        """Normalize category string to IssueCategory enum."""
        category_lower = category_str.lower().strip()

        # Try direct mapping
        for key, value in self.CATEGORY_MAPPINGS.items():
            if key in category_lower:
                return value

        # Try to infer from description
        desc_lower = description.lower()
        for key, value in self.CATEGORY_MAPPINGS.items():
            if key in desc_lower:
                return value

        return IssueCategory.EXECUTION_ISSUE

    def _normalize_discipline(self, discipline_str: str, description: str) -> LessonDiscipline:
        """Normalize discipline string to LessonDiscipline enum."""
        discipline_lower = discipline_str.lower().strip()

        for key, value in self.DISCIPLINE_MAPPINGS.items():
            if key in discipline_lower:
                return value

        # Try to infer from description
        desc_lower = description.lower()
        for key, value in self.DISCIPLINE_MAPPINGS.items():
            if key in desc_lower:
                return value

        return LessonDiscipline.GENERAL

    def _normalize_severity(self, severity_str: str) -> LessonSeverity:
        """Normalize severity string to LessonSeverity enum."""
        severity_lower = severity_str.lower().strip()

        for key, value in self.SEVERITY_MAPPINGS.items():
            if key in severity_lower:
                return value

        return LessonSeverity.MEDIUM

    def create_sample_lessons(
        self,
        reported_by: str = "system"
    ) -> LessonImportResult:
        """
        Create a set of sample lessons learned for demonstration.

        Args:
            reported_by: User creating the lessons

        Returns:
            Import result
        """
        logger.info("Creating sample lessons learned")

        lessons = [
            LessonImport(
                lesson_code="LL-2024-001",
                title="Foundation Settlement Due to Inadequate Compaction",
                project_name="ABC Industrial Complex",
                discipline=LessonDiscipline.CIVIL,
                deliverable_type="foundation_design",
                issue_category=IssueCategory.QUALITY_DEFECT,
                issue_description="Settlement of 25mm observed in isolated footing F-12 within 6 months of construction. Building showed visible cracks in superstructure. Investigation revealed inadequate compaction of backfill material around foundation.",
                root_cause="Backfill was done without proper compaction testing. Contractor used unsuitable fill material with high clay content. No compaction equipment was used for layers exceeding 300mm thickness.",
                solution="Re-excavated affected area, removed unsuitable material, replaced with approved granular fill in 150mm layers with 95% MDD compaction verified by field density tests. Underpinning of footing with micropiles to stabilize settlement.",
                preventive_measures=[
                    "Mandate compaction testing for every 150mm layer of backfill",
                    "Specify material requirements for backfill in tender documents",
                    "Include hold points for QC inspection before backfilling",
                    "Use plate load test to verify bearing capacity before footing placement"
                ],
                cost_impact=Decimal("450000"),
                schedule_impact_days=28,
                severity=LessonSeverity.CRITICAL,
                tags=["foundation", "settlement", "compaction", "backfill", "quality"],
                applicable_to=["foundation_design"],
                source="Project Closeout Report - ABC Industrial Complex"
            ),
            LessonImport(
                lesson_code="LL-2024-002",
                title="Rebar Congestion Causing Concrete Honeycomb",
                project_name="XYZ Residential Tower",
                discipline=LessonDiscipline.STRUCTURAL,
                deliverable_type="beam_design",
                issue_category=IssueCategory.DESIGN_ERROR,
                issue_description="Multiple transfer beams showed honeycomb defects after formwork removal. Investigation found severe rebar congestion at beam-column junction preventing proper concrete flow. Affected 8 beams requiring repair.",
                root_cause="Design drawings showed high reinforcement ratio (4.5%) at junction without detailing bar arrangement. Main bars from both directions overlapped in same zone. No provision for concrete vibrator access.",
                solution="Grouted affected areas after exposing honeycombed concrete. For remaining beams, redesigned junction detail using mechanical couplers instead of lap splices, staggered bar termination points, and specified concrete with 20mm aggregate.",
                preventive_measures=[
                    "Mandatory buildability review for congested reinforcement zones",
                    "Specify minimum clear spacing in design drawings",
                    "Use 3D BIM coordination for rebar clash detection",
                    "Consider mechanical couplers when reinforcement ratio exceeds 3%",
                    "Mock-up for critical sections before production"
                ],
                cost_impact=Decimal("280000"),
                schedule_impact_days=21,
                severity=LessonSeverity.HIGH,
                tags=["rebar", "congestion", "honeycomb", "beam", "junction", "buildability"],
                applicable_to=["beam_design", "column_design"],
                source="NCR Records - XYZ Residential Tower"
            ),
            LessonImport(
                lesson_code="LL-2024-003",
                title="Formwork Collapse During Slab Casting",
                project_name="PQR Commercial Building",
                discipline=LessonDiscipline.STRUCTURAL,
                deliverable_type="slab_design",
                issue_category=IssueCategory.SAFETY,
                issue_description="Formwork for 250mm thick slab at Level 3 collapsed during concrete pour. Two workers injured (minor). Approximately 15 cubic meters of concrete wasted. Investigation revealed inadequate propping system.",
                root_cause="Contractor used props rated for 150mm slab without recalculating for 250mm. Props were placed at 1.5m spacing instead of required 1.0m. No structural calculation submitted for formwork system. Site engineer did not verify propping adequacy.",
                solution="Redesigned formwork using heavy-duty props with 0.8m spacing. Engaged specialized formwork consultant. Implemented mandatory formwork design approval process before any slab pour.",
                preventive_measures=[
                    "Require formwork design calculation signed by qualified engineer",
                    "Include formwork specifications in tender documents",
                    "Pre-pour inspection checklist mandatory before concrete",
                    "Safety training on formwork for all site personnel",
                    "Regular third-party formwork audits"
                ],
                cost_impact=Decimal("180000"),
                schedule_impact_days=14,
                severity=LessonSeverity.CRITICAL,
                tags=["formwork", "collapse", "safety", "propping", "slab"],
                applicable_to=["slab_design"],
                source="Incident Investigation Report - PQR Commercial Building"
            ),
            LessonImport(
                lesson_code="LL-2024-004",
                title="Steel Column Base Plate Mismatch with Foundation",
                project_name="LMN Warehouse",
                discipline=LessonDiscipline.STRUCTURAL,
                deliverable_type="steel_column_design",
                issue_category=IssueCategory.COORDINATION_ISSUE,
                issue_description="During steel erection, found that anchor bolt pattern on 12 foundation pedestals did not match steel column base plates. Bolt holes misaligned by 50-80mm. Delayed steel erection by 3 weeks.",
                root_cause="Civil foundation drawings (Rev 2) and steel fabrication drawings (Rev 1) were not coordinated. Foundation contractor worked from superseded drawing. No interdisciplinary drawing coordination meeting held.",
                solution="Core-drilled new anchor bolt holes in affected pedestals. Used chemical anchors with increased embedment. Some columns required field-welded base plate stiffeners due to eccentric anchors.",
                preventive_measures=[
                    "Mandatory IDC (Inter-Discipline Coordination) review before construction",
                    "Single source of truth for anchor bolt coordinates",
                    "Survey verification of anchor bolts before steel fabrication",
                    "Include tolerance requirements in specifications",
                    "BIM-based coordination for steel-concrete interfaces"
                ],
                cost_impact=Decimal("320000"),
                schedule_impact_days=21,
                severity=LessonSeverity.HIGH,
                tags=["steel", "foundation", "coordination", "anchor bolts", "base plate"],
                applicable_to=["steel_column_design", "foundation_design"],
                source="Project Lessons Learned - LMN Warehouse"
            ),
            LessonImport(
                lesson_code="LL-2024-005",
                title="Overestimated Soil Bearing Capacity",
                project_name="RST School Building",
                discipline=LessonDiscipline.CIVIL,
                deliverable_type="foundation_design",
                issue_category=IssueCategory.DESIGN_ERROR,
                issue_description="Foundation designed for SBC of 200 kN/m². During excavation, actual soil found to be soft clay with SBC around 80 kN/m². Required complete foundation redesign from isolated to raft foundation.",
                root_cause="Geotechnical investigation based on only 2 boreholes for 2000 sqm building. Boreholes located in fill area showing higher capacity. Actual building footprint had different soil profile. Client approved minimum scope soil investigation to save cost.",
                solution="Redesigned to raft foundation with ground improvement using sand drains. Added 4 additional boreholes to confirm soil profile across site. Foundation cost increased by 60%.",
                preventive_measures=[
                    "Minimum borehole requirement: 1 per 500 sqm or 4 per building",
                    "Locate boreholes at actual column positions",
                    "Include CPT/SPT testing in soil investigation",
                    "Factor of safety 3.0 for preliminary design",
                    "Verify soil conditions during excavation before concreting"
                ],
                cost_impact=Decimal("850000"),
                schedule_impact_days=35,
                severity=LessonSeverity.CRITICAL,
                tags=["soil", "bearing capacity", "geotechnical", "foundation", "investigation"],
                applicable_to=["foundation_design"],
                source="Design Review Meeting Minutes - RST School Building"
            ),
        ]

        return self.lesson_service.import_lessons(
            LessonImportRequest(
                lessons=lessons,
                overwrite_existing=False,
                reported_by=reported_by
            )
        )
