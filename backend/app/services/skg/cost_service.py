"""
Cost Database Service for the Strategic Knowledge Graph.

Provides functionality for:
- Managing cost catalogs and items
- Regional cost adjustments
- Semantic search for cost data
- Cost versioning and audit trail
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.schemas.skg.cost_models import (
    CostCatalog,
    CostCatalogCreate,
    CostCatalogUpdate,
    CostCategory,
    CostItem,
    CostItemCreate,
    CostItemUpdate,
    CostImportRequest,
    CostImportResult,
    CostSearchRequest,
    CostSearchResult,
    RegionalCostResult,
    RegionalFactor,
    RegionalFactorCreate,
)

logger = logging.getLogger(__name__)


class CostDatabaseService:
    """Service for managing cost databases in the Strategic Knowledge Graph."""

    def __init__(self, embedding_service=None):
        """
        Initialize the cost database service.

        Args:
            embedding_service: Optional embedding service for vector search.
                              If not provided, will be initialized lazily.
        """
        self.db = DatabaseConfig()
        self._embedding_service = embedding_service

    @property
    def embedding_service(self):
        """Lazy initialization of embedding service."""
        if self._embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    # =========================================================================
    # CATALOG MANAGEMENT
    # =========================================================================

    def create_catalog(
        self,
        data: CostCatalogCreate,
        created_by: str
    ) -> CostCatalog:
        """
        Create a new cost catalog.

        Args:
            data: Catalog creation data
            created_by: User creating the catalog

        Returns:
            Created cost catalog
        """
        catalog_id = uuid4()

        query = """
        INSERT INTO cost_database_catalogs (
            id, catalog_name, catalog_type, description,
            base_year, base_region, currency, metadata,
            created_by, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        RETURNING *
        """

        params = (
            str(catalog_id),
            data.catalog_name,
            data.catalog_type.value,
            data.description,
            data.base_year,
            data.base_region,
            data.currency,
            json.dumps(data.metadata),
            created_by,
        )

        result = self.db.execute_query_dict(query, params)

        # Log audit
        self.db.log_audit(
            user_id=created_by,
            action="create_cost_catalog",
            entity_type="cost_catalog",
            entity_id=str(catalog_id),
            details={"catalog_name": data.catalog_name, "catalog_type": data.catalog_type.value}
        )

        logger.info(f"Created cost catalog: {data.catalog_name} ({catalog_id})")
        return CostCatalog(**result[0])

    def get_catalog(self, catalog_id: UUID) -> Optional[CostCatalog]:
        """Get a cost catalog by ID."""
        query = """
        SELECT c.*,
               (SELECT COUNT(*) FROM cost_items WHERE catalog_id = c.id AND is_active = true) as item_count
        FROM cost_database_catalogs c
        WHERE c.id = %s AND c.is_active = true
        """
        result = self.db.execute_query_dict(query, (str(catalog_id),))
        return CostCatalog(**result[0]) if result else None

    def get_catalog_by_name(self, catalog_name: str) -> Optional[CostCatalog]:
        """Get a cost catalog by name."""
        query = """
        SELECT c.*,
               (SELECT COUNT(*) FROM cost_items WHERE catalog_id = c.id AND is_active = true) as item_count
        FROM cost_database_catalogs c
        WHERE c.catalog_name = %s AND c.is_active = true
        """
        result = self.db.execute_query_dict(query, (catalog_name,))
        return CostCatalog(**result[0]) if result else None

    def list_catalogs(
        self,
        catalog_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[CostCatalog]:
        """List all cost catalogs."""
        query = """
        SELECT c.*,
               (SELECT COUNT(*) FROM cost_items WHERE catalog_id = c.id AND is_active = true) as item_count
        FROM cost_database_catalogs c
        WHERE 1=1
        """
        params = []

        if not include_inactive:
            query += " AND c.is_active = true"

        if catalog_type:
            query += " AND c.catalog_type = %s"
            params.append(catalog_type)

        query += " ORDER BY c.catalog_name"

        result = self.db.execute_query_dict(query, tuple(params) if params else None)
        return [CostCatalog(**row) for row in result]

    def update_catalog(
        self,
        catalog_id: UUID,
        data: CostCatalogUpdate,
        updated_by: str
    ) -> Optional[CostCatalog]:
        """Update a cost catalog."""
        updates = []
        params = []

        if data.catalog_name is not None:
            updates.append("catalog_name = %s")
            params.append(data.catalog_name)
        if data.description is not None:
            updates.append("description = %s")
            params.append(data.description)
        if data.base_year is not None:
            updates.append("base_year = %s")
            params.append(data.base_year)
        if data.base_region is not None:
            updates.append("base_region = %s")
            params.append(data.base_region)
        if data.currency is not None:
            updates.append("currency = %s")
            params.append(data.currency)
        if data.metadata is not None:
            updates.append("metadata = %s")
            params.append(json.dumps(data.metadata))
        if data.is_active is not None:
            updates.append("is_active = %s")
            params.append(data.is_active)

        if not updates:
            return self.get_catalog(catalog_id)

        params.append(str(catalog_id))

        query = f"""
        UPDATE cost_database_catalogs
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if result:
            self.db.log_audit(
                user_id=updated_by,
                action="update_cost_catalog",
                entity_type="cost_catalog",
                entity_id=str(catalog_id),
                details={"updates": data.model_dump(exclude_none=True)}
            )

        return CostCatalog(**result[0]) if result else None

    # =========================================================================
    # COST ITEM MANAGEMENT
    # =========================================================================

    def create_cost_item(
        self,
        data: CostItemCreate,
        created_by: str,
        generate_embedding: bool = True
    ) -> CostItem:
        """
        Create a new cost item.

        Args:
            data: Cost item data
            created_by: User creating the item
            generate_embedding: Whether to generate vector embedding

        Returns:
            Created cost item
        """
        item_id = uuid4()

        query = """
        INSERT INTO cost_items (
            id, catalog_id, item_code, item_name, category, sub_category,
            unit, base_cost, min_cost, max_cost, cost_drivers,
            specifications, source, confidence, valid_from, valid_until,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        RETURNING *
        """

        params = (
            str(item_id),
            str(data.catalog_id),
            data.item_code,
            data.item_name,
            data.category.value,
            data.sub_category,
            data.unit.value,
            float(data.base_cost),
            float(data.min_cost) if data.min_cost else None,
            float(data.max_cost) if data.max_cost else None,
            json.dumps(data.cost_drivers),
            json.dumps(data.specifications),
            data.source,
            data.confidence,
            data.valid_from,
            data.valid_until,
        )

        result = self.db.execute_query_dict(query, params)
        item = CostItem(**result[0])

        # Generate embedding for semantic search
        if generate_embedding:
            self._create_cost_embedding(item)

        self.db.log_audit(
            user_id=created_by,
            action="create_cost_item",
            entity_type="cost_item",
            entity_id=str(item_id),
            details={"item_code": data.item_code, "category": data.category.value}
        )

        logger.info(f"Created cost item: {data.item_code} ({item_id})")
        return item

    def _create_cost_embedding(self, item: CostItem) -> None:
        """Generate and store embedding for a cost item."""
        try:
            # Create searchable text from item data
            search_text = self._build_cost_search_text(item)

            # Generate embedding
            embedding = self.embedding_service.generate_embedding(search_text)

            # Store embedding
            query = """
            INSERT INTO cost_knowledge_vectors (id, cost_item_id, search_text, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cost_item_id) DO UPDATE
            SET search_text = EXCLUDED.search_text,
                embedding = EXCLUDED.embedding,
                created_at = NOW()
            """

            params = (
                str(uuid4()),
                str(item.id),
                search_text,
                embedding,
                json.dumps({"category": item.category.value, "unit": item.unit.value})
            )

            self.db.execute_query_dict(query, params)
            logger.debug(f"Created embedding for cost item: {item.item_code}")

        except Exception as e:
            logger.error(f"Failed to create embedding for cost item {item.id}: {e}")

    def _build_cost_search_text(self, item: CostItem) -> str:
        """Build searchable text from cost item data."""
        parts = [
            f"Cost item: {item.item_name}",
            f"Code: {item.item_code}",
            f"Category: {item.category.value}",
        ]

        if item.sub_category:
            parts.append(f"Subcategory: {item.sub_category}")

        parts.append(f"Unit: {item.unit.value}")
        parts.append(f"Base cost: {item.base_cost}")

        # Add specifications
        if item.specifications:
            for key, value in item.specifications.items():
                parts.append(f"{key}: {value}")

        return " | ".join(parts)

    def get_cost_item(self, item_id: UUID) -> Optional[CostItem]:
        """Get a cost item by ID."""
        query = "SELECT * FROM cost_items WHERE id = %s AND is_active = true"
        result = self.db.execute_query_dict(query, (str(item_id),))
        return CostItem(**result[0]) if result else None

    def get_cost_item_by_code(
        self,
        catalog_id: UUID,
        item_code: str
    ) -> Optional[CostItem]:
        """Get a cost item by catalog and code."""
        query = """
        SELECT * FROM cost_items
        WHERE catalog_id = %s AND item_code = %s AND is_active = true
        """
        result = self.db.execute_query_dict(query, (str(catalog_id), item_code))
        return CostItem(**result[0]) if result else None

    def list_cost_items(
        self,
        catalog_id: Optional[UUID] = None,
        category: Optional[CostCategory] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CostItem]:
        """List cost items with optional filters."""
        query = "SELECT * FROM cost_items WHERE is_active = true"
        params = []

        if catalog_id:
            query += " AND catalog_id = %s"
            params.append(str(catalog_id))

        if category:
            query += " AND category = %s"
            params.append(category.value)

        query += " ORDER BY category, item_code LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = self.db.execute_query_dict(query, tuple(params))
        return [CostItem(**row) for row in result]

    def update_cost_item(
        self,
        item_id: UUID,
        data: CostItemUpdate,
        updated_by: str
    ) -> Optional[CostItem]:
        """Update a cost item with version tracking."""
        # Get current item for version history
        current_item = self.get_cost_item(item_id)
        if not current_item:
            return None

        updates = []
        params = []

        if data.item_name is not None:
            updates.append("item_name = %s")
            params.append(data.item_name)
        if data.category is not None:
            updates.append("category = %s")
            params.append(data.category.value)
        if data.sub_category is not None:
            updates.append("sub_category = %s")
            params.append(data.sub_category)
        if data.unit is not None:
            updates.append("unit = %s")
            params.append(data.unit.value)
        if data.base_cost is not None:
            updates.append("base_cost = %s")
            params.append(float(data.base_cost))
        if data.min_cost is not None:
            updates.append("min_cost = %s")
            params.append(float(data.min_cost))
        if data.max_cost is not None:
            updates.append("max_cost = %s")
            params.append(float(data.max_cost))
        if data.cost_drivers is not None:
            updates.append("cost_drivers = %s")
            params.append(json.dumps(data.cost_drivers))
        if data.specifications is not None:
            updates.append("specifications = %s")
            params.append(json.dumps(data.specifications))
        if data.source is not None:
            updates.append("source = %s")
            params.append(data.source)
        if data.confidence is not None:
            updates.append("confidence = %s")
            params.append(data.confidence)
        if data.valid_from is not None:
            updates.append("valid_from = %s")
            params.append(data.valid_from)
        if data.valid_until is not None:
            updates.append("valid_until = %s")
            params.append(data.valid_until)
        if data.is_active is not None:
            updates.append("is_active = %s")
            params.append(data.is_active)

        if not updates:
            return current_item

        # Create version record if cost changed
        if data.base_cost is not None and data.base_cost != current_item.base_cost:
            self._create_cost_version(
                item_id=item_id,
                previous_cost=current_item.base_cost,
                new_cost=data.base_cost,
                change_reason=data.change_reason,
                changed_by=updated_by
            )

        params.append(str(item_id))

        query = f"""
        UPDATE cost_items
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if result:
            updated_item = CostItem(**result[0])

            # Update embedding
            self._create_cost_embedding(updated_item)

            self.db.log_audit(
                user_id=updated_by,
                action="update_cost_item",
                entity_type="cost_item",
                entity_id=str(item_id),
                details={
                    "change_reason": data.change_reason,
                    "updates": data.model_dump(exclude_none=True, exclude={"change_reason"})
                }
            )

            return updated_item

        return None

    def _create_cost_version(
        self,
        item_id: UUID,
        previous_cost: Decimal,
        new_cost: Decimal,
        change_reason: str,
        changed_by: str
    ) -> None:
        """Create a version record for cost changes."""
        # Get current version number
        query = """
        SELECT COALESCE(MAX(version_number), 0) + 1 as next_version
        FROM cost_item_versions
        WHERE cost_item_id = %s
        """
        result = self.db.execute_query_dict(query, (str(item_id),))
        next_version = result[0]["next_version"]

        # Insert version record
        query = """
        INSERT INTO cost_item_versions (
            id, cost_item_id, version_number, previous_cost, new_cost,
            change_reason, changed_by, changed_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """

        params = (
            str(uuid4()),
            str(item_id),
            next_version,
            float(previous_cost),
            float(new_cost),
            change_reason,
            changed_by
        )

        self.db.execute_query_dict(query, params)
        logger.debug(f"Created version {next_version} for cost item {item_id}")

    # =========================================================================
    # REGIONAL FACTORS
    # =========================================================================

    def create_regional_factor(
        self,
        data: RegionalFactorCreate,
        created_by: str
    ) -> RegionalFactor:
        """Create a regional cost adjustment factor."""
        factor_id = uuid4()

        query = """
        INSERT INTO regional_cost_factors (
            id, catalog_id, region_name, region_code, category,
            adjustment_factor, adjustment_reason, metadata, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING *
        """

        params = (
            str(factor_id),
            str(data.catalog_id),
            data.region_name,
            data.region_code,
            data.category.value if data.category else None,
            float(data.adjustment_factor),
            data.adjustment_reason,
            json.dumps(data.metadata),
        )

        result = self.db.execute_query_dict(query, params)

        self.db.log_audit(
            user_id=created_by,
            action="create_regional_factor",
            entity_type="regional_factor",
            entity_id=str(factor_id),
            details={"region_code": data.region_code, "factor": float(data.adjustment_factor)}
        )

        return RegionalFactor(**result[0])

    def get_regional_factors(
        self,
        catalog_id: UUID,
        region_code: Optional[str] = None
    ) -> List[RegionalFactor]:
        """Get regional factors for a catalog."""
        query = """
        SELECT * FROM regional_cost_factors
        WHERE catalog_id = %s AND is_active = true
        """
        params = [str(catalog_id)]

        if region_code:
            query += " AND region_code = %s"
            params.append(region_code)

        query += " ORDER BY region_code, category"

        result = self.db.execute_query_dict(query, tuple(params))
        return [RegionalFactor(**row) for row in result]

    def get_regional_cost(
        self,
        item_id: UUID,
        region_code: str
    ) -> Optional[RegionalCostResult]:
        """Get cost adjusted for a specific region."""
        query = "SELECT * FROM get_regional_cost(%s, %s)"
        result = self.db.execute_query_dict(query, (str(item_id), region_code))

        if result:
            row = result[0]
            return RegionalCostResult(
                item_name=row["item_name"],
                base_cost=Decimal(str(row["base_cost"])),
                adjustment_factor=Decimal(str(row["adjustment_factor"])),
                adjusted_cost=Decimal(str(row["adjusted_cost"])),
                unit=row["unit"],
                region_code=region_code
            )
        return None

    # =========================================================================
    # SEMANTIC SEARCH
    # =========================================================================

    def search_costs(
        self,
        request: CostSearchRequest,
        user_id: str
    ) -> List[CostSearchResult]:
        """
        Search cost items using semantic search.

        Args:
            request: Search request with query and filters
            user_id: User performing the search

        Returns:
            List of matching cost items with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(request.query)

        # Use database function for search
        query = """
        SELECT * FROM search_cost_items(
            %s::vector,
            %s,
            %s,
            %s,
            %s
        )
        """

        params = (
            query_embedding,
            request.limit,
            request.category.value if request.category else None,
            str(request.catalog_id) if request.catalog_id else None,
            request.min_confidence
        )

        result = self.db.execute_query_dict(query, params)

        # Apply regional adjustment if requested
        search_results = []
        for row in result:
            adjusted_cost = None
            if request.region_code:
                regional = self.get_regional_cost(
                    UUID(row["cost_item_id"]),
                    request.region_code
                )
                if regional:
                    adjusted_cost = regional.adjusted_cost

            search_results.append(CostSearchResult(
                cost_item_id=UUID(row["cost_item_id"]),
                item_code=row["item_code"],
                item_name=row["item_name"],
                category=row["category"],
                base_cost=Decimal(str(row["base_cost"])),
                adjusted_cost=adjusted_cost,
                unit=row["unit"],
                specifications=row["specifications"] or {},
                similarity=float(row["similarity"]),
                confidence=request.min_confidence
            ))

        # Log audit
        self.db.log_audit(
            user_id=user_id,
            action="search_costs",
            entity_type="cost_search",
            entity_id="search",
            details={"query": request.query, "results_count": len(search_results)}
        )

        return search_results

    # =========================================================================
    # BULK IMPORT
    # =========================================================================

    def import_costs(
        self,
        request: CostImportRequest
    ) -> CostImportResult:
        """
        Bulk import cost items.

        Args:
            request: Import request with items and options

        Returns:
            Import result with counts and errors
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for item in request.items:
            try:
                existing = self.get_cost_item_by_code(
                    request.catalog_id,
                    item.item_code
                )

                if existing:
                    if request.overwrite_existing:
                        # Update existing
                        self.update_cost_item(
                            existing.id,
                            CostItemUpdate(
                                item_name=item.item_name,
                                category=item.category,
                                sub_category=item.sub_category,
                                unit=item.unit,
                                base_cost=item.base_cost,
                                min_cost=item.min_cost,
                                max_cost=item.max_cost,
                                specifications=item.specifications,
                                source=item.source,
                                change_reason="Bulk import update"
                            ),
                            request.created_by
                        )
                        updated += 1
                    else:
                        skipped += 1
                else:
                    # Create new
                    self.create_cost_item(
                        CostItemCreate(
                            catalog_id=request.catalog_id,
                            item_code=item.item_code,
                            item_name=item.item_name,
                            category=item.category,
                            sub_category=item.sub_category,
                            unit=item.unit,
                            base_cost=item.base_cost,
                            min_cost=item.min_cost,
                            max_cost=item.max_cost,
                            specifications=item.specifications,
                            source=item.source
                        ),
                        request.created_by
                    )
                    created += 1

            except Exception as e:
                errors.append({
                    "item_code": item.item_code,
                    "error": str(e)
                })
                logger.error(f"Failed to import cost item {item.item_code}: {e}")

        logger.info(
            f"Cost import complete: {created} created, {updated} updated, "
            f"{skipped} skipped, {len(errors)} errors"
        )

        return CostImportResult(
            total_items=len(request.items),
            items_created=created,
            items_updated=updated,
            items_skipped=skipped,
            errors=errors
        )
