"""
Pydantic models for Knowledge Relationships in the Strategic Knowledge Graph.

These models handle relationships between:
- Cost items
- Constructability rules
- Lessons learned

Relationships enable the "graph" aspect of the Strategic Knowledge Graph,
allowing discovery of related knowledge across different entity types.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class KnowledgeEntityType(str, Enum):
    """Types of knowledge entities in the graph."""
    COST_ITEM = "cost_item"
    RULE = "rule"
    LESSON = "lesson"


class RelationshipType(str, Enum):
    """Types of relationships between entities."""
    IMPACTS = "impacts"           # Source impacts target (e.g., rule impacts cost)
    RELATED_TO = "related_to"     # General relationship
    SUPERSEDES = "supersedes"     # Source replaces target
    DERIVED_FROM = "derived_from" # Source was derived from target
    PREVENTS = "prevents"         # Source prevents issues in target
    CAUSED_BY = "caused_by"       # Source was caused by target


# =============================================================================
# RELATIONSHIP MODELS
# =============================================================================

class KnowledgeRelationshipCreate(BaseModel):
    """Model for creating a knowledge relationship."""
    source_type: KnowledgeEntityType
    source_id: UUID
    target_type: KnowledgeEntityType
    target_id: UUID
    relationship_type: RelationshipType
    strength: Decimal = Field(
        default=Decimal("0.5"),
        ge=0,
        le=1,
        description="Strength of relationship (0-1)"
    )
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: str

    @model_validator(mode='after')
    def validate_not_self_referential(self):
        """Ensure source and target are different."""
        if self.source_type == self.target_type and self.source_id == self.target_id:
            raise ValueError("Cannot create relationship to self")
        return self


class KnowledgeRelationship(KnowledgeRelationshipCreate):
    """Complete knowledge relationship model."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class RelationshipWithDetails(BaseModel):
    """Relationship with details about source and target entities."""
    id: UUID
    source_type: KnowledgeEntityType
    source_id: UUID
    source_name: str  # Name/title of source entity
    target_type: KnowledgeEntityType
    target_id: UUID
    target_name: str  # Name/title of target entity
    relationship_type: RelationshipType
    strength: Decimal
    description: Optional[str]


# =============================================================================
# GRAPH QUERY MODELS
# =============================================================================

class RelatedEntityRequest(BaseModel):
    """Request model for finding related entities."""
    entity_type: KnowledgeEntityType
    entity_id: UUID
    relationship_types: Optional[List[RelationshipType]] = Field(
        None,
        description="Filter by relationship types"
    )
    target_types: Optional[List[KnowledgeEntityType]] = Field(
        None,
        description="Filter by target entity types"
    )
    min_strength: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        le=1,
        description="Minimum relationship strength"
    )
    include_reverse: bool = Field(
        True,
        description="Include relationships where entity is target"
    )
    limit: int = Field(20, ge=1, le=100)


class RelatedEntity(BaseModel):
    """A related entity in the knowledge graph."""
    entity_type: KnowledgeEntityType
    entity_id: UUID
    entity_name: str
    entity_summary: Optional[str] = None
    relationship_type: RelationshipType
    relationship_direction: str = Field(description="'outgoing' or 'incoming'")
    strength: Decimal


class RelatedEntitiesResponse(BaseModel):
    """Response model for related entities query."""
    source_type: KnowledgeEntityType
    source_id: UUID
    source_name: str
    total_relationships: int
    related_entities: List[RelatedEntity]


# =============================================================================
# KNOWLEDGE GRAPH TRAVERSAL
# =============================================================================

class GraphPathRequest(BaseModel):
    """Request model for finding paths between entities."""
    start_type: KnowledgeEntityType
    start_id: UUID
    end_type: KnowledgeEntityType
    end_id: UUID
    max_depth: int = Field(3, ge=1, le=5, description="Maximum path length")
    relationship_types: Optional[List[RelationshipType]] = None


class GraphPathNode(BaseModel):
    """A node in a graph path."""
    entity_type: KnowledgeEntityType
    entity_id: UUID
    entity_name: str


class GraphPathEdge(BaseModel):
    """An edge in a graph path."""
    relationship_type: RelationshipType
    strength: Decimal
    direction: str  # 'forward' or 'reverse'


class GraphPath(BaseModel):
    """A path through the knowledge graph."""
    nodes: List[GraphPathNode]
    edges: List[GraphPathEdge]
    total_strength: Decimal = Field(description="Product of edge strengths")
    path_length: int


class GraphPathResponse(BaseModel):
    """Response model for path finding."""
    start_entity: GraphPathNode
    end_entity: GraphPathNode
    paths_found: int
    paths: List[GraphPath]


# =============================================================================
# KNOWLEDGE GRAPH STATISTICS
# =============================================================================

class GraphStatistics(BaseModel):
    """Statistics about the knowledge graph."""
    total_cost_items: int
    total_rules: int
    total_lessons: int
    total_relationships: int
    relationships_by_type: Dict[str, int]
    avg_relationships_per_entity: float
    most_connected_entities: List[Dict[str, Any]]
    recently_added: Dict[str, int]


# =============================================================================
# BULK RELATIONSHIP OPERATIONS
# =============================================================================

class BulkRelationshipCreate(BaseModel):
    """Model for creating multiple relationships."""
    relationships: List[KnowledgeRelationshipCreate] = Field(
        ...,
        min_length=1,
        max_length=100
    )


class BulkRelationshipResult(BaseModel):
    """Result of bulk relationship creation."""
    total_submitted: int
    relationships_created: int
    relationships_skipped: int
    errors: List[Dict[str, str]]
