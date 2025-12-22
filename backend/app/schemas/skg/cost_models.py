"""
Pydantic models for Cost Database Management in the Strategic Knowledge Graph.

These models handle:
- Cost catalogs (collections of cost data)
- Individual cost items (materials, labor, equipment)
- Regional adjustment factors
- Cost search and retrieval
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class CostCategory(str, Enum):
    """Categories for cost items."""
    CONCRETE = "concrete"
    STEEL = "steel"
    FORMWORK = "formwork"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    EXCAVATION = "excavation"
    BACKFILL = "backfill"
    WATERPROOFING = "waterproofing"
    FINISHING = "finishing"
    MISC = "misc"


class CostUnit(str, Enum):
    """Units for cost measurement."""
    PER_CUM = "per_cum"        # Per cubic meter
    PER_SQM = "per_sqm"        # Per square meter
    PER_KG = "per_kg"          # Per kilogram
    PER_M = "per_m"            # Per meter
    PER_ITEM = "per_item"      # Per item/piece
    PER_DAY = "per_day"        # Per day (labor/equipment)
    PER_HOUR = "per_hour"      # Per hour
    PER_TONNE = "per_tonne"    # Per tonne
    LUMPSUM = "lumpsum"        # Lumpsum amount


class CatalogType(str, Enum):
    """Types of cost catalogs."""
    STANDARD = "standard"           # Standard rate schedule
    REGIONAL = "regional"           # Region-specific rates
    PROJECT_SPECIFIC = "project_specific"  # Project-specific rates
    LEARNED = "learned"             # Rates learned from projects


# =============================================================================
# COST ITEM MODELS
# =============================================================================

class CostItemBase(BaseModel):
    """Base model for cost items."""
    item_code: str = Field(..., min_length=1, max_length=50, description="Unique item code")
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name/description")
    category: CostCategory = Field(..., description="Cost category")
    sub_category: Optional[str] = Field(None, max_length=100, description="Sub-category")
    unit: CostUnit = Field(..., description="Unit of measurement")
    base_cost: Decimal = Field(..., gt=0, description="Base cost per unit")
    min_cost: Optional[Decimal] = Field(None, ge=0, description="Minimum expected cost")
    max_cost: Optional[Decimal] = Field(None, ge=0, description="Maximum expected cost")
    cost_drivers: Dict[str, Any] = Field(default_factory=dict, description="Factors affecting cost")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    source: Optional[str] = Field(None, max_length=200, description="Data source")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence in the cost data")
    valid_from: Optional[date] = Field(None, description="Date from which cost is valid")
    valid_until: Optional[date] = Field(None, description="Date until which cost is valid")

    @model_validator(mode='after')
    def validate_cost_range(self):
        """Ensure min_cost <= base_cost <= max_cost."""
        if self.min_cost is not None and self.base_cost < self.min_cost:
            raise ValueError("base_cost must be >= min_cost")
        if self.max_cost is not None and self.base_cost > self.max_cost:
            raise ValueError("base_cost must be <= max_cost")
        if self.min_cost is not None and self.max_cost is not None:
            if self.min_cost > self.max_cost:
                raise ValueError("min_cost must be <= max_cost")
        return self


class CostItemCreate(CostItemBase):
    """Model for creating a new cost item."""
    catalog_id: UUID = Field(..., description="Parent catalog ID")


class CostItemUpdate(BaseModel):
    """Model for updating a cost item."""
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[CostCategory] = None
    sub_category: Optional[str] = Field(None, max_length=100)
    unit: Optional[CostUnit] = None
    base_cost: Optional[Decimal] = Field(None, gt=0)
    min_cost: Optional[Decimal] = Field(None, ge=0)
    max_cost: Optional[Decimal] = Field(None, ge=0)
    cost_drivers: Optional[Dict[str, Any]] = None
    specifications: Optional[Dict[str, Any]] = None
    source: Optional[str] = Field(None, max_length=200)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None
    change_reason: str = Field(..., min_length=1, description="Reason for the update")


class CostItem(CostItemBase):
    """Complete cost item model with database fields."""
    id: UUID
    catalog_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# COST CATALOG MODELS
# =============================================================================

class CostCatalogBase(BaseModel):
    """Base model for cost catalogs."""
    catalog_name: str = Field(..., min_length=1, max_length=100, description="Catalog name")
    catalog_type: CatalogType = Field(..., description="Type of catalog")
    description: Optional[str] = Field(None, max_length=500)
    base_year: int = Field(default=2024, ge=2000, le=2100)
    base_region: str = Field(default="india", max_length=50)
    currency: str = Field(default="INR", max_length=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostCatalogCreate(CostCatalogBase):
    """Model for creating a new cost catalog."""
    pass


class CostCatalogUpdate(BaseModel):
    """Model for updating a cost catalog."""
    catalog_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_year: Optional[int] = Field(None, ge=2000, le=2100)
    base_region: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CostCatalog(CostCatalogBase):
    """Complete cost catalog model with database fields."""
    id: UUID
    is_active: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime
    item_count: Optional[int] = None  # Computed field

    class Config:
        from_attributes = True


# =============================================================================
# REGIONAL FACTOR MODELS
# =============================================================================

class RegionalFactorCreate(BaseModel):
    """Model for creating regional cost adjustment factors."""
    catalog_id: UUID = Field(..., description="Parent catalog ID")
    region_name: str = Field(..., min_length=1, max_length=100)
    region_code: str = Field(..., min_length=1, max_length=20)
    category: Optional[CostCategory] = Field(None, description="Applies to specific category, or all if None")
    adjustment_factor: Decimal = Field(..., gt=0, le=5.0, description="Multiplier for base cost")
    adjustment_reason: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegionalFactor(RegionalFactorCreate):
    """Complete regional factor model."""
    id: UUID
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# SEARCH AND RESULT MODELS
# =============================================================================

class CostSearchRequest(BaseModel):
    """Request model for cost search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    category: Optional[CostCategory] = Field(None, description="Filter by category")
    catalog_id: Optional[UUID] = Field(None, description="Filter by catalog")
    region_code: Optional[str] = Field(None, description="Apply regional adjustment")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100)


class CostSearchResult(BaseModel):
    """Result model for cost search."""
    cost_item_id: UUID
    item_code: str
    item_name: str
    category: str
    base_cost: Decimal
    adjusted_cost: Optional[Decimal] = None  # If region_code provided
    unit: str
    specifications: Dict[str, Any]
    similarity: float
    confidence: float


class RegionalCostResult(BaseModel):
    """Result model for regional cost lookup."""
    item_name: str
    base_cost: Decimal
    adjustment_factor: Decimal
    adjusted_cost: Decimal
    unit: str
    region_code: str
    region_name: Optional[str] = None


# =============================================================================
# BULK IMPORT MODELS
# =============================================================================

class CostItemImport(BaseModel):
    """Model for bulk importing cost items."""
    item_code: str
    item_name: str
    category: CostCategory
    sub_category: Optional[str] = None
    unit: CostUnit
    base_cost: Decimal
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


class CostImportRequest(BaseModel):
    """Request model for bulk cost import."""
    catalog_id: UUID
    items: List[CostItemImport] = Field(..., min_length=1, max_length=1000)
    overwrite_existing: bool = Field(False, description="Overwrite existing items with same code")
    created_by: str


class CostImportResult(BaseModel):
    """Result model for bulk cost import."""
    total_items: int
    items_created: int
    items_updated: int
    items_skipped: int
    errors: List[Dict[str, str]]
