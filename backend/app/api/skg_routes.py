"""
API Routes for the Strategic Knowledge Graph (SKG).

Provides endpoints for:
- Cost Database Management
- Constructability Rules
- Lessons Learned
- Knowledge Relationships
- Graph Statistics
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel, Field

from app.schemas.skg.cost_models import (
    CostCatalog,
    CostCatalogCreate,
    CostCatalogUpdate,
    CostCategory,
    CostItem,
    CostItemCreate,
    CostItemUpdate,
    CostSearchRequest,
    CostSearchResult,
    RegionalCostResult,
    RegionalFactorCreate,
    RegionalFactor,
)
from app.schemas.skg.rule_models import (
    ConstructabilityRule,
    RuleCategory,
    RuleCategoryCreate,
    RuleCreate,
    RuleDiscipline,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
    RuleSearchRequest,
    RuleSearchResult,
    RuleSeverity,
    RuleType,
    RuleUpdate,
)
from app.schemas.skg.lesson_models import (
    IssueCategory,
    LessonAnalytics,
    LessonApplication,
    LessonApplicationCreate,
    LessonApplicationUpdate,
    LessonCreate,
    LessonDiscipline,
    LessonLearned,
    LessonSearchRequest,
    LessonSearchResult,
    LessonSeverity,
    LessonSummary,
    LessonUpdate,
)
from app.schemas.skg.relationship_models import (
    GraphStatistics,
    KnowledgeEntityType,
    KnowledgeRelationship,
    KnowledgeRelationshipCreate,
    RelatedEntitiesResponse,
    RelatedEntityRequest,
    RelationshipType,
)
from app.services.skg import (
    CostDatabaseService,
    ConstructabilityRuleService,
    LessonsLearnedService,
    KnowledgeRelationshipService,
)

# Initialize router
router = APIRouter(prefix="/api/v1/skg", tags=["Strategic Knowledge Graph"])

# Initialize services (lazy loading)
_cost_service: Optional[CostDatabaseService] = None
_rule_service: Optional[ConstructabilityRuleService] = None
_lesson_service: Optional[LessonsLearnedService] = None
_relationship_service: Optional[KnowledgeRelationshipService] = None


def get_cost_service() -> CostDatabaseService:
    global _cost_service
    if _cost_service is None:
        _cost_service = CostDatabaseService()
    return _cost_service


def get_rule_service() -> ConstructabilityRuleService:
    global _rule_service
    if _rule_service is None:
        _rule_service = ConstructabilityRuleService()
    return _rule_service


def get_lesson_service() -> LessonsLearnedService:
    global _lesson_service
    if _lesson_service is None:
        _lesson_service = LessonsLearnedService()
    return _lesson_service


def get_relationship_service() -> KnowledgeRelationshipService:
    global _relationship_service
    if _relationship_service is None:
        _relationship_service = KnowledgeRelationshipService()
    return _relationship_service


# =============================================================================
# COST DATABASE ENDPOINTS
# =============================================================================

@router.post("/costs/catalogs", response_model=CostCatalog)
async def create_cost_catalog(
    data: CostCatalogCreate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a new cost catalog."""
    try:
        service = get_cost_service()
        return service.create_catalog(data, x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/catalogs", response_model=List[CostCatalog])
async def list_cost_catalogs(
    catalog_type: Optional[str] = None,
    include_inactive: bool = False
):
    """List all cost catalogs."""
    service = get_cost_service()
    return service.list_catalogs(catalog_type, include_inactive)


@router.get("/costs/catalogs/{catalog_id}", response_model=CostCatalog)
async def get_cost_catalog(catalog_id: UUID):
    """Get a cost catalog by ID."""
    service = get_cost_service()
    catalog = service.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return catalog


@router.put("/costs/catalogs/{catalog_id}", response_model=CostCatalog)
async def update_cost_catalog(
    catalog_id: UUID,
    data: CostCatalogUpdate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update a cost catalog."""
    service = get_cost_service()
    result = service.update_catalog(catalog_id, data, x_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return result


@router.post("/costs/items", response_model=CostItem)
async def create_cost_item(
    data: CostItemCreate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a new cost item."""
    try:
        service = get_cost_service()
        return service.create_cost_item(data, x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/items", response_model=List[CostItem])
async def list_cost_items(
    catalog_id: Optional[UUID] = None,
    category: Optional[CostCategory] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List cost items with optional filters."""
    service = get_cost_service()
    return service.list_cost_items(catalog_id, category, limit, offset)


@router.get("/costs/items/{item_id}", response_model=CostItem)
async def get_cost_item(item_id: UUID):
    """Get a cost item by ID."""
    service = get_cost_service()
    item = service.get_cost_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    return item


@router.put("/costs/items/{item_id}", response_model=CostItem)
async def update_cost_item(
    item_id: UUID,
    data: CostItemUpdate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update a cost item."""
    service = get_cost_service()
    result = service.update_cost_item(item_id, data, x_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cost item not found")
    return result


@router.post("/costs/search", response_model=List[CostSearchResult])
async def search_costs(
    request: CostSearchRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Search cost items using semantic search."""
    service = get_cost_service()
    return service.search_costs(request, x_user_id)


@router.get("/costs/items/{item_id}/regional/{region_code}", response_model=RegionalCostResult)
async def get_regional_cost(item_id: UUID, region_code: str):
    """Get cost adjusted for a specific region."""
    service = get_cost_service()
    result = service.get_regional_cost(item_id, region_code)
    if not result:
        raise HTTPException(status_code=404, detail="Cost item or region not found")
    return result


@router.post("/costs/regional-factors", response_model=RegionalFactor)
async def create_regional_factor(
    data: RegionalFactorCreate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a regional cost adjustment factor."""
    service = get_cost_service()
    return service.create_regional_factor(data, x_user_id)


@router.get("/costs/regional-factors/{catalog_id}", response_model=List[RegionalFactor])
async def get_regional_factors(
    catalog_id: UUID,
    region_code: Optional[str] = None
):
    """Get regional factors for a catalog."""
    service = get_cost_service()
    return service.get_regional_factors(catalog_id, region_code)


# =============================================================================
# CONSTRUCTABILITY RULES ENDPOINTS
# =============================================================================

@router.post("/rules/categories", response_model=RuleCategory)
async def create_rule_category(
    data: RuleCategoryCreate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a rule category."""
    service = get_rule_service()
    return service.create_category(data, x_user_id)


@router.get("/rules/categories", response_model=List[RuleCategory])
async def list_rule_categories():
    """List all rule categories."""
    service = get_rule_service()
    return service.list_categories()


@router.post("/rules", response_model=ConstructabilityRule)
async def create_rule(data: RuleCreate):
    """Create a new constructability rule."""
    try:
        service = get_rule_service()
        return service.create_rule(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=List[ConstructabilityRule])
async def list_rules(
    discipline: Optional[RuleDiscipline] = None,
    rule_type: Optional[RuleType] = None,
    severity: Optional[RuleSeverity] = None,
    enabled_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List constructability rules with optional filters."""
    service = get_rule_service()
    return service.list_rules(discipline, rule_type, severity, enabled_only, limit, offset)


@router.get("/rules/{rule_id}", response_model=ConstructabilityRule)
async def get_rule(rule_id: UUID):
    """Get a rule by ID."""
    service = get_rule_service()
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("/rules/code/{rule_code}", response_model=ConstructabilityRule)
async def get_rule_by_code(rule_code: str):
    """Get a rule by code."""
    service = get_rule_service()
    rule = service.get_rule_by_code(rule_code)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=ConstructabilityRule)
async def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update a constructability rule."""
    service = get_rule_service()
    result = service.update_rule(rule_id, data, x_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.post("/rules/evaluate", response_model=RuleEvaluationResponse)
async def evaluate_rules(
    request: RuleEvaluationRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Evaluate applicable rules against input data."""
    service = get_rule_service()
    return service.evaluate_rules(request, x_user_id)


@router.post("/rules/search", response_model=List[RuleSearchResult])
async def search_rules(
    request: RuleSearchRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Search rules using semantic search."""
    service = get_rule_service()
    return service.search_rules(request, x_user_id)


# =============================================================================
# LESSONS LEARNED ENDPOINTS
# =============================================================================

@router.post("/lessons", response_model=LessonLearned)
async def create_lesson(data: LessonCreate):
    """Create a new lesson learned."""
    try:
        service = get_lesson_service()
        return service.create_lesson(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lessons", response_model=List[LessonSummary])
async def list_lessons(
    discipline: Optional[LessonDiscipline] = None,
    issue_category: Optional[IssueCategory] = None,
    severity: Optional[LessonSeverity] = None,
    deliverable_type: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List lessons learned with optional filters."""
    service = get_lesson_service()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return service.list_lessons(
        discipline, issue_category, severity, deliverable_type,
        tags=tag_list, limit=limit, offset=offset
    )


@router.get("/lessons/{lesson_id}", response_model=LessonLearned)
async def get_lesson(lesson_id: UUID):
    """Get a lesson by ID."""
    service = get_lesson_service()
    lesson = service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/lessons/code/{lesson_code}", response_model=LessonLearned)
async def get_lesson_by_code(lesson_code: str):
    """Get a lesson by code."""
    service = get_lesson_service()
    lesson = service.get_lesson_by_code(lesson_code)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.put("/lessons/{lesson_id}", response_model=LessonLearned)
async def update_lesson(
    lesson_id: UUID,
    data: LessonUpdate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update a lesson learned."""
    service = get_lesson_service()
    result = service.update_lesson(lesson_id, data, x_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return result


@router.post("/lessons/search", response_model=List[LessonSearchResult])
async def search_lessons(
    request: LessonSearchRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Search lessons using semantic search."""
    service = get_lesson_service()
    return service.search_lessons(request, x_user_id)


@router.get("/lessons/relevant/{workflow_type}", response_model=List[LessonSearchResult])
async def get_relevant_lessons(
    workflow_type: str,
    discipline: Optional[LessonDiscipline] = None,
    context: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Get lessons relevant to a workflow context."""
    service = get_lesson_service()
    return service.get_relevant_lessons(workflow_type, discipline, context, limit, x_user_id)


@router.post("/lessons/{lesson_id}/apply", response_model=LessonApplication)
async def record_lesson_application(
    lesson_id: UUID,
    data: LessonApplicationCreate
):
    """Record when a lesson is applied."""
    service = get_lesson_service()
    return service.record_application(data)


@router.put("/lessons/applications/{application_id}/feedback", response_model=LessonApplication)
async def update_application_feedback(
    application_id: UUID,
    data: LessonApplicationUpdate,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update feedback for a lesson application."""
    service = get_lesson_service()
    result = service.update_application_feedback(application_id, data, x_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.get("/lessons/{lesson_id}/applications", response_model=List[LessonApplication])
async def get_lesson_applications(
    lesson_id: UUID,
    limit: int = Query(50, ge=1, le=200)
):
    """Get applications of a specific lesson."""
    service = get_lesson_service()
    return service.get_lesson_applications(lesson_id, limit)


@router.get("/lessons/analytics", response_model=LessonAnalytics)
async def get_lesson_analytics():
    """Get analytics for lessons learned."""
    service = get_lesson_service()
    return service.get_analytics()


# =============================================================================
# KNOWLEDGE RELATIONSHIPS ENDPOINTS
# =============================================================================

@router.post("/relationships", response_model=KnowledgeRelationship)
async def create_relationship(data: KnowledgeRelationshipCreate):
    """Create a relationship between knowledge entities."""
    try:
        service = get_relationship_service()
        return service.create_relationship(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/{relationship_id}", response_model=KnowledgeRelationship)
async def get_relationship(relationship_id: UUID):
    """Get a relationship by ID."""
    service = get_relationship_service()
    rel = service.get_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: UUID,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Delete a relationship."""
    service = get_relationship_service()
    success = service.delete_relationship(relationship_id, x_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"status": "deleted", "relationship_id": str(relationship_id)}


@router.post("/relationships/related", response_model=RelatedEntitiesResponse)
async def get_related_entities(request: RelatedEntityRequest):
    """Get entities related to a given entity."""
    service = get_relationship_service()
    return service.get_related_entities(request)


# =============================================================================
# GRAPH STATISTICS ENDPOINT
# =============================================================================

@router.get("/statistics", response_model=GraphStatistics)
async def get_graph_statistics():
    """Get statistics about the Strategic Knowledge Graph."""
    service = get_relationship_service()
    return service.get_statistics()


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def skg_health_check():
    """Health check for Strategic Knowledge Graph services."""
    try:
        # Check database connectivity
        service = get_relationship_service()
        stats = service.get_statistics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "cost_items": stats.total_cost_items,
                "rules": stats.total_rules,
                "lessons": stats.total_lessons,
                "relationships": stats.total_relationships
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
