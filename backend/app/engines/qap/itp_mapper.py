"""
Phase 4 Sprint 4: ITP Mapping Service

This module maps extracted scope items to standard Inspection Test Plans (ITPs)
from the template library. The mapping uses:
1. Category matching
2. Keyword similarity scoring
3. Knowledge base vector search (if available)

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

from app.engines.qap.models import (
    ScopeItem,
    ScopeItemCategory,
    ITPMappingInput,
    ITPMappingResult,
    ITPMatch,
    QualityLevel,
)
from app.engines.qap.itp_templates import (
    ITP_TEMPLATES,
    get_templates_by_category,
    get_templates_by_keywords,
    ITPTemplate,
)


# =============================================================================
# KEYWORD MATCHING CONFIGURATION
# =============================================================================

# Additional keyword synonyms for better matching
KEYWORD_SYNONYMS = {
    "piling": ["pile", "piles", "bored pile", "driven pile", "CFA", "auger"],
    "concrete": ["rcc", "reinforced concrete", "casting", "concreting", "cement"],
    "precast": ["pre-cast", "prefabricated", "precast element", "precast panel"],
    "steel": ["structural steel", "steel structure", "steelwork", "fabrication"],
    "excavation": ["digging", "cutting", "bulk excavation", "trench"],
    "waterproofing": ["membrane", "tanking", "dampproofing", "water proofing"],
    "electrical": ["wiring", "cable", "conduit", "power", "lighting"],
    "plumbing": ["piping", "drainage", "water supply", "sanitary"],
    "masonry": ["brickwork", "blockwork", "brick", "block", "AAC"],
    "plastering": ["plaster", "rendering", "cement plaster"],
    "tiling": ["tiles", "flooring", "vitrified", "ceramic"],
    "foundation": ["footing", "raft", "mat foundation", "pile cap"],
}


# =============================================================================
# MAIN MAPPING FUNCTION
# =============================================================================

def map_scope_to_itps(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map scope items to relevant ITPs.

    This function analyzes each scope item and finds the most relevant
    ITP templates based on category, keywords, and semantic matching.

    Args:
        input_data: Dictionary matching ITPMappingInput schema

    Returns:
        Dictionary matching ITPMappingResult schema

    Example:
        >>> input_data = {
        ...     "scope_items": [{"id": "SI-001", "description": "Bored piling works", ...}],
        ...     "quality_level": "major"
        ... }
        >>> result = map_scope_to_itps(input_data)
        >>> result["coverage_percentage"]
        85.0
    """
    # Validate input
    data = ITPMappingInput(**input_data)

    print(f"[ITP MAPPER] Mapping {len(data.scope_items)} scope items to ITPs")

    mappings: List[ITPMatch] = []
    unmapped_items: List[str] = []
    itp_ids_used = set()

    for scope_item in data.scope_items:
        matches = _find_matching_itps(scope_item, data.include_optional)

        if matches:
            # Take the best match(es) for this scope item
            for match in matches:
                mappings.append(match)
                itp_ids_used.add(match.itp_id)
        else:
            unmapped_items.append(f"{scope_item.id}: {scope_item.description}")
            print(f"[ITP MAPPER] No ITP found for: {scope_item.description}")

    # Calculate coverage
    total_items = len(data.scope_items)
    mapped_items = total_items - len(unmapped_items)
    coverage = (mapped_items / total_items * 100) if total_items > 0 else 0

    # Generate recommendations for unmapped items
    recommendations = _generate_recommendations(unmapped_items, data.scope_items)

    result = ITPMappingResult(
        total_scope_items=total_items,
        total_itps_mapped=len(itp_ids_used),
        mappings=mappings,
        unmapped_items=unmapped_items,
        coverage_percentage=round(coverage, 1),
        recommendations=recommendations
    )

    print(f"[ITP MAPPER] Mapped {mapped_items}/{total_items} items ({coverage:.1f}% coverage)")
    print(f"[ITP MAPPER] Total unique ITPs: {len(itp_ids_used)}")

    return result.model_dump()


def _find_matching_itps(
    scope_item: ScopeItem,
    include_optional: bool = False
) -> List[ITPMatch]:
    """
    Find matching ITPs for a scope item.

    Uses multi-stage matching:
    1. Category-based matching
    2. Keyword-based matching
    3. Description text analysis

    Args:
        scope_item: The scope item to match
        include_optional: Whether to include optional/related ITPs

    Returns:
        List of ITPMatch objects
    """
    matches: List[Tuple[ITPTemplate, float, str]] = []

    # Extract matching keywords from scope item
    item_keywords = set(kw.lower() for kw in scope_item.keywords)
    item_description = scope_item.description.lower()

    # Add synonyms to keywords
    expanded_keywords = set(item_keywords)
    for kw in item_keywords:
        if kw in KEYWORD_SYNONYMS:
            expanded_keywords.update(KEYWORD_SYNONYMS[kw])

    # Stage 1: Category match
    category_templates = get_templates_by_category(scope_item.category)

    for template in category_templates:
        score, reason = _calculate_match_score(
            scope_item, template, expanded_keywords, item_description
        )
        if score > 0.3:  # Minimum threshold
            matches.append((template, score, reason))

    # Stage 2: Keyword match (may find templates from other categories)
    if scope_item.keywords:
        keyword_templates = get_templates_by_keywords(list(expanded_keywords))

        for template in keyword_templates:
            # Skip if already matched
            if any(m[0].itp_id == template.itp_id for m in matches):
                continue

            score, reason = _calculate_match_score(
                scope_item, template, expanded_keywords, item_description
            )
            if score > 0.4:  # Slightly higher threshold for cross-category
                matches.append((template, score, reason))

    # Stage 3: Text analysis (for items without clear matches)
    if not matches or max(m[1] for m in matches) < 0.5:
        text_matches = _text_based_matching(scope_item, expanded_keywords)
        matches.extend(text_matches)

    # Sort by score and take top matches
    matches.sort(key=lambda x: x[1], reverse=True)

    # Convert to ITPMatch objects
    result: List[ITPMatch] = []

    # Always include the best match if score > threshold
    for template, score, reason in matches[:3]:  # Top 3 matches
        if score < 0.3:
            continue

        # Determine if mandatory based on quality level
        is_mandatory = (
            scope_item.priority == QualityLevel.CRITICAL or
            score > 0.7
        )

        # Suggest customizations
        customizations = _suggest_customizations(scope_item, template)

        result.append(ITPMatch(
            scope_item_id=scope_item.id,
            scope_item_description=scope_item.description,
            itp_id=template.itp_id,
            itp_name=template.itp_name,
            match_score=round(score, 2),
            match_reason=reason,
            is_mandatory=is_mandatory,
            customizations=customizations
        ))

        # If not including optional, just take the best mandatory match
        if not include_optional and is_mandatory:
            break

    return result


def _calculate_match_score(
    scope_item: ScopeItem,
    template: ITPTemplate,
    expanded_keywords: set,
    item_description: str
) -> Tuple[float, str]:
    """
    Calculate match score between scope item and ITP template.

    Args:
        scope_item: The scope item
        template: The ITP template
        expanded_keywords: Expanded keywords from scope item
        item_description: Lowercase description

    Returns:
        Tuple of (score, reason)
    """
    score = 0.0
    reasons = []

    # Category match (0.3 weight)
    if scope_item.category == template.category:
        score += 0.3
        reasons.append("category match")

    # Keyword match (0.4 weight)
    template_keywords = set(k.lower() for k in template.keywords)
    template_applicable = set(a.lower() for a in template.applicable_to)
    all_template_terms = template_keywords | template_applicable

    keyword_overlap = expanded_keywords & all_template_terms
    if keyword_overlap:
        keyword_score = min(len(keyword_overlap) / max(len(expanded_keywords), 1), 1.0)
        score += keyword_score * 0.4
        reasons.append(f"keywords: {', '.join(list(keyword_overlap)[:3])}")

    # Description text match (0.3 weight)
    desc_matches = 0
    for term in all_template_terms:
        if term in item_description:
            desc_matches += 1

    if desc_matches > 0:
        desc_score = min(desc_matches / max(len(all_template_terms), 1), 1.0)
        score += desc_score * 0.3
        reasons.append("description match")

    # Subcategory bonus
    if scope_item.sub_category and template.sub_category:
        if scope_item.sub_category.lower() == template.sub_category.lower():
            score += 0.1
            reasons.append("subcategory match")

    reason = "; ".join(reasons) if reasons else "partial match"

    return min(score, 1.0), reason


def _text_based_matching(
    scope_item: ScopeItem,
    expanded_keywords: set
) -> List[Tuple[ITPTemplate, float, str]]:
    """
    Perform text-based matching when keyword matching is insufficient.

    Args:
        scope_item: The scope item
        expanded_keywords: Expanded keywords

    Returns:
        List of (template, score, reason) tuples
    """
    matches = []
    description = scope_item.description.lower()

    # Define text patterns and their ITP mappings
    text_patterns = [
        (r'pile|piling|bore', "ITP-PIL-001", 0.6, "text pattern: pile work"),
        (r'load\s*test|pile\s*test', "ITP-PIL-002", 0.7, "text pattern: load test"),
        (r'rcc|reinforced|concrete\s*(?:work|pour|cast)', "ITP-CON-001", 0.6, "text pattern: RCC work"),
        (r'pre[\-\s]?cast', "ITP-CON-002", 0.7, "text pattern: precast"),
        (r'steel\s*(?:structure|work|fabrication)|structural\s*steel', "ITP-STL-001", 0.6, "text pattern: steel work"),
        (r'excavat|cutting|digg', "ITP-EW-001", 0.5, "text pattern: excavation"),
        (r'fill|compact|backfill', "ITP-EW-002", 0.5, "text pattern: filling"),
        (r'water\s*proof|membrane|tank', "ITP-WP-001", 0.6, "text pattern: waterproofing"),
        (r'electric|wiring|cable|power', "ITP-MEP-001", 0.5, "text pattern: electrical"),
        (r'plumb|pipe|drain|sanitary', "ITP-MEP-002", 0.5, "text pattern: plumbing"),
        (r'brick|block|masonry', "ITP-MAS-001", 0.5, "text pattern: masonry"),
        (r'plaster|render', "ITP-FIN-001", 0.5, "text pattern: plastering"),
        (r'tile|floor|vitrified|ceramic', "ITP-FIN-002", 0.5, "text pattern: tiling"),
    ]

    for pattern, itp_id, base_score, reason in text_patterns:
        if re.search(pattern, description):
            template = ITP_TEMPLATES.get(itp_id)
            if template:
                matches.append((template, base_score, reason))

    return matches


def _suggest_customizations(
    scope_item: ScopeItem,
    template: ITPTemplate
) -> Dict[str, Any]:
    """
    Suggest customizations for the ITP based on scope item details.

    Args:
        scope_item: The scope item
        template: The matched ITP template

    Returns:
        Dictionary of suggested customizations
    """
    customizations = {}

    # Add location-specific notes
    if scope_item.location:
        customizations["location_applicability"] = scope_item.location

    # Add quantity information
    if scope_item.quantity:
        customizations["quantity_note"] = f"Quantity: {scope_item.quantity}"

    # Add specification references
    if scope_item.specifications:
        customizations["additional_reference"] = scope_item.specifications

    # Adjust quality level if scope item has different priority
    if scope_item.priority == QualityLevel.CRITICAL:
        customizations["quality_emphasis"] = "All checkpoints to be treated as HOLD points"

    return customizations


def _generate_recommendations(
    unmapped_items: List[str],
    all_scope_items: List[ScopeItem]
) -> List[str]:
    """
    Generate recommendations for improving coverage.

    Args:
        unmapped_items: List of unmapped item descriptions
        all_scope_items: All scope items

    Returns:
        List of recommendation strings
    """
    recommendations = []

    if not unmapped_items:
        recommendations.append("100% scope coverage achieved with standard ITPs")
        return recommendations

    # Analyze unmapped items
    unmapped_count = len(unmapped_items)
    total_count = len(all_scope_items)

    if unmapped_count > 0:
        recommendations.append(
            f"{unmapped_count} scope items require custom ITPs or manual review"
        )

    # Check for patterns in unmapped items
    unmapped_text = " ".join(unmapped_items).lower()

    if "hvac" in unmapped_text or "air condition" in unmapped_text:
        recommendations.append(
            "Consider adding ITP for HVAC installation (currently not in standard library)"
        )

    if "fire" in unmapped_text:
        recommendations.append(
            "Consider adding ITP for Fire Protection systems"
        )

    if "landscape" in unmapped_text or "horticulture" in unmapped_text:
        recommendations.append(
            "Consider adding ITP for Landscaping/Horticulture works"
        )

    if "signage" in unmapped_text or "graphics" in unmapped_text:
        recommendations.append(
            "Consider adding ITP for Signage and Graphics"
        )

    # General recommendations
    if unmapped_count > total_count * 0.3:  # More than 30% unmapped
        recommendations.append(
            "High number of unmapped items - consider expanding ITP template library"
        )

    recommendations.append(
        "Review unmapped items with QA team to create project-specific ITPs"
    )

    return recommendations


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_itp_coverage_summary(mapping_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of ITP coverage by category.

    Args:
        mapping_result: Result from map_scope_to_itps

    Returns:
        Coverage summary dictionary
    """
    category_coverage = {}

    for mapping in mapping_result.get("mappings", []):
        template = ITP_TEMPLATES.get(mapping["itp_id"])
        if template:
            cat = template.category.value
            if cat not in category_coverage:
                category_coverage[cat] = {
                    "mapped_items": 0,
                    "itps_used": set()
                }
            category_coverage[cat]["mapped_items"] += 1
            category_coverage[cat]["itps_used"].add(mapping["itp_id"])

    # Convert sets to counts
    for cat in category_coverage:
        category_coverage[cat]["itps_used"] = len(category_coverage[cat]["itps_used"])

    return {
        "by_category": category_coverage,
        "total_coverage": mapping_result.get("coverage_percentage", 0),
        "total_itps": mapping_result.get("total_itps_mapped", 0)
    }


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Test with sample scope items
    from app.engines.qap.models import ScopeItem

    sample_items = [
        ScopeItem(
            id="SI-001",
            description="Bored cast-in-situ piling - 600mm diameter, 15m depth",
            category=ScopeItemCategory.PILING,
            keywords=["bored pile", "piling", "foundation"],
            priority=QualityLevel.CRITICAL
        ),
        ScopeItem(
            id="SI-002",
            description="RCC columns and beams for superstructure",
            category=ScopeItemCategory.CONCRETE,
            keywords=["rcc", "concrete", "column", "beam"],
            priority=QualityLevel.CRITICAL
        ),
        ScopeItem(
            id="SI-003",
            description="Basement waterproofing with APP membrane",
            category=ScopeItemCategory.WATERPROOFING,
            keywords=["waterproofing", "membrane", "basement"],
            priority=QualityLevel.MAJOR
        ),
        ScopeItem(
            id="SI-004",
            description="External brick masonry with fly ash bricks",
            category=ScopeItemCategory.MASONRY,
            keywords=["brick", "masonry"],
            priority=QualityLevel.MINOR
        ),
    ]

    test_input = {
        "scope_items": [item.model_dump() for item in sample_items],
        "quality_level": "major",
        "include_optional": True
    }

    result = map_scope_to_itps(test_input)

    print("\n" + "="*60)
    print("ITP MAPPING RESULT")
    print("="*60)
    print(f"Total Scope Items: {result['total_scope_items']}")
    print(f"Total ITPs Mapped: {result['total_itps_mapped']}")
    print(f"Coverage: {result['coverage_percentage']}%")

    print("\nMappings:")
    for m in result['mappings']:
        print(f"  {m['scope_item_id']} -> {m['itp_id']} ({m['match_score']:.2f})")
        print(f"    Reason: {m['match_reason']}")

    if result['unmapped_items']:
        print("\nUnmapped Items:")
        for item in result['unmapped_items']:
            print(f"  - {item}")

    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")
