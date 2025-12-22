"""
Cost Data Ingestion Pipeline for the Strategic Knowledge Graph.

Supports ingestion from:
- CSV files (standard rate schedules)
- JSON files (structured cost data)
- Manual entry via API
"""

import csv
import json
import logging
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.skg.cost_models import (
    CatalogType,
    CostCategory,
    CostCatalogCreate,
    CostImportRequest,
    CostImportResult,
    CostItemImport,
    CostUnit,
    RegionalFactorCreate,
)
from app.services.skg.cost_service import CostDatabaseService

logger = logging.getLogger(__name__)


class CostDataIngestion:
    """ETL pipeline for ingesting cost data into the Strategic Knowledge Graph."""

    # Mapping of common CSV column names to our schema
    COLUMN_MAPPINGS = {
        # Item code
        "item_code": ["item_code", "code", "item_no", "sr_no", "sl_no", "id"],
        # Item name
        "item_name": ["item_name", "description", "item_description", "name", "material"],
        # Category
        "category": ["category", "type", "item_type", "material_type"],
        # Unit
        "unit": ["unit", "uom", "unit_of_measurement"],
        # Base cost
        "base_cost": ["base_cost", "rate", "unit_rate", "cost", "price", "amount"],
        # Min cost
        "min_cost": ["min_cost", "min_rate", "minimum"],
        # Max cost
        "max_cost": ["max_cost", "max_rate", "maximum"],
        # Sub category
        "sub_category": ["sub_category", "subcategory", "sub_type"],
        # Source
        "source": ["source", "reference", "ref"],
    }

    # Category normalization
    CATEGORY_MAPPINGS = {
        "concrete": CostCategory.CONCRETE,
        "cement": CostCategory.CONCRETE,
        "rcc": CostCategory.CONCRETE,
        "steel": CostCategory.STEEL,
        "reinforcement": CostCategory.STEEL,
        "rebar": CostCategory.STEEL,
        "tmt": CostCategory.STEEL,
        "formwork": CostCategory.FORMWORK,
        "shuttering": CostCategory.FORMWORK,
        "centering": CostCategory.FORMWORK,
        "labor": CostCategory.LABOR,
        "labour": CostCategory.LABOR,
        "manpower": CostCategory.LABOR,
        "equipment": CostCategory.EQUIPMENT,
        "machinery": CostCategory.EQUIPMENT,
        "plant": CostCategory.EQUIPMENT,
        "excavation": CostCategory.EXCAVATION,
        "earthwork": CostCategory.EXCAVATION,
        "digging": CostCategory.EXCAVATION,
        "backfill": CostCategory.BACKFILL,
        "filling": CostCategory.BACKFILL,
        "waterproofing": CostCategory.WATERPROOFING,
        "wp": CostCategory.WATERPROOFING,
        "finishing": CostCategory.FINISHING,
        "plastering": CostCategory.FINISHING,
        "painting": CostCategory.FINISHING,
    }

    # Unit normalization
    UNIT_MAPPINGS = {
        "cum": CostUnit.PER_CUM,
        "m3": CostUnit.PER_CUM,
        "cubic meter": CostUnit.PER_CUM,
        "sqm": CostUnit.PER_SQM,
        "m2": CostUnit.PER_SQM,
        "square meter": CostUnit.PER_SQM,
        "kg": CostUnit.PER_KG,
        "kilogram": CostUnit.PER_KG,
        "m": CostUnit.PER_M,
        "rm": CostUnit.PER_M,
        "rmt": CostUnit.PER_M,
        "meter": CostUnit.PER_M,
        "running meter": CostUnit.PER_M,
        "no": CostUnit.PER_ITEM,
        "nos": CostUnit.PER_ITEM,
        "each": CostUnit.PER_ITEM,
        "piece": CostUnit.PER_ITEM,
        "pcs": CostUnit.PER_ITEM,
        "day": CostUnit.PER_DAY,
        "per day": CostUnit.PER_DAY,
        "hour": CostUnit.PER_HOUR,
        "hr": CostUnit.PER_HOUR,
        "per hour": CostUnit.PER_HOUR,
        "tonne": CostUnit.PER_TONNE,
        "ton": CostUnit.PER_TONNE,
        "mt": CostUnit.PER_TONNE,
        "ls": CostUnit.LUMPSUM,
        "lumpsum": CostUnit.LUMPSUM,
        "lump sum": CostUnit.LUMPSUM,
    }

    def __init__(self, cost_service: Optional[CostDatabaseService] = None):
        """
        Initialize the cost data ingestion pipeline.

        Args:
            cost_service: Optional cost service instance
        """
        self.cost_service = cost_service or CostDatabaseService()

    def ingest_from_csv(
        self,
        file_path: str,
        catalog_name: str,
        catalog_type: CatalogType = CatalogType.STANDARD,
        created_by: str = "system",
        base_year: int = 2024,
        base_region: str = "india",
        overwrite_existing: bool = False
    ) -> CostImportResult:
        """
        Ingest cost data from a CSV file.

        Expected CSV format:
        item_code,item_name,category,unit,base_cost[,min_cost,max_cost,sub_category,source]

        Args:
            file_path: Path to CSV file
            catalog_name: Name for the cost catalog
            catalog_type: Type of catalog
            created_by: User performing the import
            base_year: Base year for costs
            base_region: Base region for costs
            overwrite_existing: Whether to overwrite existing items

        Returns:
            Import result with counts and errors
        """
        logger.info(f"Ingesting cost data from CSV: {file_path}")

        # Read and parse CSV
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        with open(path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        return self._process_csv_content(
            content,
            catalog_name,
            catalog_type,
            created_by,
            base_year,
            base_region,
            overwrite_existing
        )

    def ingest_from_csv_string(
        self,
        csv_content: str,
        catalog_name: str,
        catalog_type: CatalogType = CatalogType.STANDARD,
        created_by: str = "system",
        base_year: int = 2024,
        base_region: str = "india",
        overwrite_existing: bool = False
    ) -> CostImportResult:
        """
        Ingest cost data from a CSV string.

        Args:
            csv_content: CSV content as string
            catalog_name: Name for the cost catalog
            catalog_type: Type of catalog
            created_by: User performing the import
            base_year: Base year for costs
            base_region: Base region for costs
            overwrite_existing: Whether to overwrite existing items

        Returns:
            Import result with counts and errors
        """
        return self._process_csv_content(
            csv_content,
            catalog_name,
            catalog_type,
            created_by,
            base_year,
            base_region,
            overwrite_existing
        )

    def _process_csv_content(
        self,
        content: str,
        catalog_name: str,
        catalog_type: CatalogType,
        created_by: str,
        base_year: int,
        base_region: str,
        overwrite_existing: bool
    ) -> CostImportResult:
        """Process CSV content and import into database."""
        # Create or get catalog
        catalog = self.cost_service.get_catalog_by_name(catalog_name)
        if not catalog:
            catalog = self.cost_service.create_catalog(
                CostCatalogCreate(
                    catalog_name=catalog_name,
                    catalog_type=catalog_type,
                    description=f"Imported from CSV - {catalog_type.value}",
                    base_year=base_year,
                    base_region=base_region
                ),
                created_by
            )
            logger.info(f"Created new catalog: {catalog_name}")

        # Parse CSV
        reader = csv.DictReader(StringIO(content))
        headers = reader.fieldnames or []

        # Map column names
        column_map = self._map_columns(headers)

        # Process rows
        items = []
        parse_errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                item = self._parse_csv_row(row, column_map, row_num)
                if item:
                    items.append(item)
            except Exception as e:
                parse_errors.append({
                    "row": row_num,
                    "error": str(e)
                })
                logger.warning(f"Failed to parse row {row_num}: {e}")

        logger.info(f"Parsed {len(items)} items from CSV ({len(parse_errors)} parse errors)")

        # Import items
        if items:
            result = self.cost_service.import_costs(
                CostImportRequest(
                    catalog_id=catalog.id,
                    items=items,
                    overwrite_existing=overwrite_existing,
                    created_by=created_by
                )
            )

            # Add parse errors to result
            result.errors.extend(parse_errors)
            return result

        return CostImportResult(
            total_items=0,
            items_created=0,
            items_updated=0,
            items_skipped=0,
            errors=parse_errors
        )

    def _map_columns(self, headers: List[str]) -> Dict[str, str]:
        """Map CSV column headers to our schema fields."""
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
    ) -> Optional[CostItemImport]:
        """Parse a single CSV row into a CostItemImport."""
        # Extract required fields
        item_code = self._get_field(row, column_map, "item_code")
        item_name = self._get_field(row, column_map, "item_name")
        base_cost_str = self._get_field(row, column_map, "base_cost")

        if not item_code or not item_name or not base_cost_str:
            raise ValueError(f"Missing required fields: item_code, item_name, or base_cost")

        # Parse base cost
        try:
            base_cost = Decimal(base_cost_str.replace(",", "").strip())
            if base_cost <= 0:
                raise ValueError("Base cost must be positive")
        except InvalidOperation:
            raise ValueError(f"Invalid base cost: {base_cost_str}")

        # Parse category
        category_str = self._get_field(row, column_map, "category") or ""
        category = self._normalize_category(category_str, item_name)

        # Parse unit
        unit_str = self._get_field(row, column_map, "unit") or ""
        unit = self._normalize_unit(unit_str)

        # Parse optional fields
        min_cost = None
        min_cost_str = self._get_field(row, column_map, "min_cost")
        if min_cost_str:
            try:
                min_cost = Decimal(min_cost_str.replace(",", "").strip())
            except InvalidOperation:
                pass

        max_cost = None
        max_cost_str = self._get_field(row, column_map, "max_cost")
        if max_cost_str:
            try:
                max_cost = Decimal(max_cost_str.replace(",", "").strip())
            except InvalidOperation:
                pass

        # Build specifications from item name
        specifications = self._extract_specifications(item_name)

        return CostItemImport(
            item_code=item_code.strip(),
            item_name=item_name.strip(),
            category=category,
            sub_category=self._get_field(row, column_map, "sub_category"),
            unit=unit,
            base_cost=base_cost,
            min_cost=min_cost,
            max_cost=max_cost,
            specifications=specifications,
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

    def _normalize_category(self, category_str: str, item_name: str) -> CostCategory:
        """Normalize category string to CostCategory enum."""
        category_lower = category_str.lower().strip()

        # Try direct mapping
        if category_lower in self.CATEGORY_MAPPINGS:
            return self.CATEGORY_MAPPINGS[category_lower]

        # Try partial match
        for key, value in self.CATEGORY_MAPPINGS.items():
            if key in category_lower:
                return value

        # Try to infer from item name
        item_lower = item_name.lower()
        for key, value in self.CATEGORY_MAPPINGS.items():
            if key in item_lower:
                return value

        # Default to misc
        return CostCategory.MISC

    def _normalize_unit(self, unit_str: str) -> CostUnit:
        """Normalize unit string to CostUnit enum."""
        unit_lower = unit_str.lower().strip()

        # Try direct mapping
        if unit_lower in self.UNIT_MAPPINGS:
            return self.UNIT_MAPPINGS[unit_lower]

        # Try partial match
        for key, value in self.UNIT_MAPPINGS.items():
            if key in unit_lower:
                return value

        # Default to per item
        return CostUnit.PER_ITEM

    def _extract_specifications(self, item_name: str) -> Dict[str, Any]:
        """Extract specifications from item name."""
        specs = {}

        # Extract concrete grade (M15, M20, M25, etc.)
        import re
        grade_match = re.search(r'\b(M\d{2})\b', item_name, re.IGNORECASE)
        if grade_match:
            specs["grade"] = grade_match.group(1).upper()

        # Extract steel grade (Fe415, Fe500, etc.)
        steel_match = re.search(r'\b(Fe\d{3})\b', item_name, re.IGNORECASE)
        if steel_match:
            specs["steel_grade"] = steel_match.group(1)

        # Extract diameter (8mm, 10mm, 12mm, etc.)
        dia_match = re.search(r'\b(\d+)\s*mm\b', item_name, re.IGNORECASE)
        if dia_match:
            specs["diameter_mm"] = int(dia_match.group(1))

        # Extract thickness
        thick_match = re.search(r'(\d+)\s*mm\s*thick', item_name, re.IGNORECASE)
        if thick_match:
            specs["thickness_mm"] = int(thick_match.group(1))

        return specs

    def ingest_from_json(
        self,
        file_path: str,
        created_by: str = "system",
        overwrite_existing: bool = False
    ) -> CostImportResult:
        """
        Ingest cost data from a JSON file.

        Expected JSON format:
        {
            "catalog": {
                "catalog_name": "...",
                "catalog_type": "standard|regional|project_specific|learned",
                "base_year": 2024,
                "base_region": "india"
            },
            "items": [
                {
                    "item_code": "...",
                    "item_name": "...",
                    "category": "concrete|steel|...",
                    "unit": "per_cum|per_kg|...",
                    "base_cost": 1000.00,
                    ...
                }
            ],
            "regional_factors": [
                {
                    "region_name": "North India",
                    "region_code": "north_india",
                    "adjustment_factor": 1.0
                }
            ]
        }

        Args:
            file_path: Path to JSON file
            created_by: User performing the import
            overwrite_existing: Whether to overwrite existing items

        Returns:
            Import result with counts and errors
        """
        logger.info(f"Ingesting cost data from JSON: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Create catalog
        catalog_data = data.get("catalog", {})
        catalog_name = catalog_data.get("catalog_name", path.stem)
        catalog_type = CatalogType(catalog_data.get("catalog_type", "standard"))

        catalog = self.cost_service.get_catalog_by_name(catalog_name)
        if not catalog:
            catalog = self.cost_service.create_catalog(
                CostCatalogCreate(
                    catalog_name=catalog_name,
                    catalog_type=catalog_type,
                    description=catalog_data.get("description"),
                    base_year=catalog_data.get("base_year", 2024),
                    base_region=catalog_data.get("base_region", "india")
                ),
                created_by
            )

        # Import items
        items_data = data.get("items", [])
        items = []
        errors = []

        for idx, item_data in enumerate(items_data):
            try:
                items.append(CostItemImport(
                    item_code=item_data["item_code"],
                    item_name=item_data["item_name"],
                    category=CostCategory(item_data["category"]),
                    sub_category=item_data.get("sub_category"),
                    unit=CostUnit(item_data["unit"]),
                    base_cost=Decimal(str(item_data["base_cost"])),
                    min_cost=Decimal(str(item_data["min_cost"])) if item_data.get("min_cost") else None,
                    max_cost=Decimal(str(item_data["max_cost"])) if item_data.get("max_cost") else None,
                    specifications=item_data.get("specifications", {}),
                    source=item_data.get("source")
                ))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "item_code": item_data.get("item_code", "unknown"),
                    "error": str(e)
                })

        result = CostImportResult(
            total_items=0,
            items_created=0,
            items_updated=0,
            items_skipped=0,
            errors=errors
        )

        if items:
            result = self.cost_service.import_costs(
                CostImportRequest(
                    catalog_id=catalog.id,
                    items=items,
                    overwrite_existing=overwrite_existing,
                    created_by=created_by
                )
            )
            result.errors.extend(errors)

        # Import regional factors
        regional_data = data.get("regional_factors", [])
        for factor_data in regional_data:
            try:
                self.cost_service.create_regional_factor(
                    RegionalFactorCreate(
                        catalog_id=catalog.id,
                        region_name=factor_data["region_name"],
                        region_code=factor_data["region_code"],
                        category=CostCategory(factor_data["category"]) if factor_data.get("category") else None,
                        adjustment_factor=Decimal(str(factor_data["adjustment_factor"])),
                        adjustment_reason=factor_data.get("adjustment_reason")
                    ),
                    created_by
                )
            except Exception as e:
                logger.warning(f"Failed to import regional factor: {e}")

        return result
