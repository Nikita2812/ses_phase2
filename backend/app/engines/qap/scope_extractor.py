"""
Phase 4 Sprint 4: Scope Extraction Service

This module extracts key scope items from Project Scope of Work documents
using LLM-based analysis. It identifies:
- Construction activities (e.g., "Piling required", "Pre-cast elements used")
- Work categories (civil, structural, architectural, MEP)
- Quantities and locations when specified
- Quality-critical items

Author: CSA AIaaS Platform
Version: 1.0
"""

import os
import re
import json
import uuid
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.engines.qap.models import (
    ScopeExtractionInput,
    ScopeExtractionResult,
    ScopeItem,
    ScopeItemCategory,
    QualityLevel,
)


# =============================================================================
# LLM PROMPT TEMPLATE
# =============================================================================

SCOPE_EXTRACTION_PROMPT = """You are an expert construction project analyst specializing in Quality Assurance Plans (QAP).
Your task is to analyze a Project Scope of Work document and extract key scope items that require quality control and inspection.

DOCUMENT TYPE: {document_type}
PROJECT NAME: {project_name}
PROJECT TYPE: {project_type}

---
DOCUMENT TEXT:
{document_text}
---

EXTRACTION INSTRUCTIONS:
1. Identify all construction activities and work items mentioned in the scope
2. Categorize each item into the appropriate category
3. Extract quantities and locations where specified
4. Identify quality-critical items that require special attention
5. Note any specific specifications or standards mentioned

CATEGORIES TO USE:
- civil: General civil works (roads, drainage, utilities)
- structural: Structural works (RCC, steel, foundations)
- architectural: Finishing, facades, interiors
- mep: Mechanical, electrical, plumbing
- geotechnical: Soil investigation, ground improvement
- earthwork: Excavation, filling, compaction
- piling: Pile foundations of any type
- concrete: Concrete works (casting, curing)
- steel: Structural steel, reinforcement
- masonry: Brick/block work
- waterproofing: Waterproofing and dampproofing
- finishing: Flooring, painting, cladding
- landscaping: Soft/hard landscaping
- utilities: Water, sewer, electrical lines
- general: General/miscellaneous items

QUALITY LEVELS:
- critical: Safety/structural integrity items (e.g., foundation piles, structural connections)
- major: Important quality requirements (e.g., concrete grade, waterproofing)
- minor: Standard quality requirements (e.g., painting, landscaping)

OUTPUT FORMAT (JSON):
{{
    "project_name": "<extracted or provided project name>",
    "project_type": "<extracted or provided project type>",
    "summary": "<2-3 sentence summary of the scope>",
    "scope_items": [
        {{
            "id": "SI-001",
            "description": "<clear description of the scope item>",
            "category": "<category from list above>",
            "sub_category": "<optional sub-category>",
            "keywords": ["keyword1", "keyword2"],
            "quantity": "<quantity if specified, e.g., '500 cu.m'>",
            "location": "<location if specified, e.g., 'Block A'>",
            "specifications": "<referenced specs, e.g., 'IS 456:2000'>",
            "priority": "<critical/major/minor>",
            "confidence": <0.0-1.0>
        }}
    ],
    "categories_found": ["category1", "category2"],
    "warnings": ["any extraction warnings"]
}}

Extract all relevant scope items. Be thorough but avoid duplicates.
Focus on items that would require quality inspection or testing.
"""


# =============================================================================
# SCOPE EXTRACTION FUNCTION
# =============================================================================

def extract_scope_items(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract scope items from a Project Scope of Work document.

    This function uses LLM analysis to identify and categorize scope items
    that require quality control and inspection.

    Args:
        input_data: Dictionary matching ScopeExtractionInput schema

    Returns:
        Dictionary matching ScopeExtractionResult schema

    Example:
        >>> input_data = {
        ...     "document_text": "Project includes piling works, RCC construction...",
        ...     "document_type": "scope_of_work",
        ...     "project_name": "ABC Commercial Complex"
        ... }
        >>> result = extract_scope_items(input_data)
        >>> result["total_items"]
        15
    """
    # Validate input
    data = ScopeExtractionInput(**input_data)

    print(f"[SCOPE EXTRACTOR] Starting extraction for project: {data.project_name or 'Unknown'}")
    print(f"[SCOPE EXTRACTOR] Document type: {data.document_type}")
    print(f"[SCOPE EXTRACTOR] Document length: {len(data.document_text)} characters")

    # Try LLM extraction first
    try:
        llm_result = _extract_with_llm(data)
        if llm_result and llm_result.get("scope_items"):
            return llm_result
    except Exception as e:
        print(f"[SCOPE EXTRACTOR] LLM extraction failed: {e}")
        print("[SCOPE EXTRACTOR] Falling back to rule-based extraction")

    # Fallback to rule-based extraction
    return _extract_with_rules(data)


def _extract_with_llm(data: ScopeExtractionInput) -> Dict[str, Any]:
    """
    Extract scope items using LLM analysis.

    Args:
        data: Validated scope extraction input

    Returns:
        Extraction result dictionary
    """
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    # Prepare prompt
    prompt = SCOPE_EXTRACTION_PROMPT.format(
        document_type=data.document_type,
        project_name=data.project_name or "Not specified",
        project_type=data.project_type or "Not specified",
        document_text=data.document_text[:15000]  # Limit document size
    )

    # Call LLM
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://csa-aiaas.com",
    }

    payload = {
        "model": "nvidia/nemotron-3-nano-30b-a3b:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
    }

    print("[SCOPE EXTRACTOR] Calling LLM for extraction...")

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

    if response.status_code != 200:
        raise ValueError(f"LLM API error: {response.status_code} - {response.text}")

    # Parse response
    result = response.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Extract JSON from response
    extracted_data = _parse_llm_response(content)

    if not extracted_data:
        raise ValueError("Failed to parse LLM response")

    # Build result
    scope_items = []
    for item_data in extracted_data.get("scope_items", []):
        try:
            # Map category string to enum
            category_str = item_data.get("category", "general").lower()
            try:
                category = ScopeItemCategory(category_str)
            except ValueError:
                category = ScopeItemCategory.GENERAL

            # Map priority string to enum
            priority_str = item_data.get("priority", "major").lower()
            try:
                priority = QualityLevel(priority_str)
            except ValueError:
                priority = QualityLevel.MAJOR

            scope_item = ScopeItem(
                id=item_data.get("id", f"SI-{len(scope_items)+1:03d}"),
                description=item_data.get("description", ""),
                category=category,
                sub_category=item_data.get("sub_category"),
                keywords=item_data.get("keywords", []),
                quantity=item_data.get("quantity"),
                location=item_data.get("location"),
                specifications=item_data.get("specifications"),
                priority=priority,
                confidence=float(item_data.get("confidence", 0.9))
            )
            scope_items.append(scope_item)
        except Exception as e:
            print(f"[SCOPE EXTRACTOR] Failed to parse item: {e}")
            continue

    result = ScopeExtractionResult(
        project_name=extracted_data.get("project_name") or data.project_name,
        project_type=extracted_data.get("project_type") or data.project_type,
        scope_items=scope_items,
        summary=extracted_data.get("summary", "Scope extraction completed"),
        total_items=len(scope_items),
        categories_found=extracted_data.get("categories_found", []),
        extraction_confidence=0.9,
        warnings=extracted_data.get("warnings", [])
    )

    print(f"[SCOPE EXTRACTOR] Extracted {len(scope_items)} scope items")
    return result.model_dump()


def _parse_llm_response(content: str) -> Optional[Dict]:
    """Parse JSON from LLM response."""
    # Try to extract JSON from response
    # Handle various formats: raw JSON, markdown code blocks, etc.

    # Try raw JSON first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object pattern
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _extract_with_rules(data: ScopeExtractionInput) -> Dict[str, Any]:
    """
    Fallback rule-based scope extraction.

    Uses keyword matching and pattern recognition to extract scope items
    when LLM is unavailable.

    Args:
        data: Validated scope extraction input

    Returns:
        Extraction result dictionary
    """
    print("[SCOPE EXTRACTOR] Using rule-based extraction")

    text = data.document_text.lower()
    scope_items = []

    # Define extraction rules: (pattern, category, keywords, priority)
    extraction_rules = [
        # Piling
        (r'(?:bored|driven|pile|piling)\s*(?:works?|foundation)?', ScopeItemCategory.PILING,
         ["piling", "pile foundation", "bored pile", "driven pile"], QualityLevel.CRITICAL),
        # Concrete/RCC
        (r'(?:rcc|reinforced\s*concrete|concrete)\s*(?:works?|structure|casting)?',
         ScopeItemCategory.CONCRETE, ["rcc", "concrete", "casting", "curing"], QualityLevel.CRITICAL),
        # Foundation
        (r'(?:foundation|footing|raft|mat)\s*(?:works?)?', ScopeItemCategory.STRUCTURAL,
         ["foundation", "footing", "raft foundation"], QualityLevel.CRITICAL),
        # Steel
        (r'(?:structural\s*steel|steel\s*(?:structure|work|fabrication))', ScopeItemCategory.STEEL,
         ["structural steel", "steel fabrication", "welding"], QualityLevel.CRITICAL),
        # Pre-cast
        (r'pre[\-\s]?cast\s*(?:elements?|concrete|panels?)?', ScopeItemCategory.CONCRETE,
         ["precast", "pre-cast elements", "precast panels"], QualityLevel.MAJOR),
        # Excavation
        (r'(?:excavation|earthwork|earth\s*work|cutting|filling)', ScopeItemCategory.EARTHWORK,
         ["excavation", "earthwork", "compaction"], QualityLevel.MAJOR),
        # Waterproofing
        (r'(?:waterproofing|damp\s*proof|membrane|tanking)', ScopeItemCategory.WATERPROOFING,
         ["waterproofing", "membrane", "dampproofing"], QualityLevel.MAJOR),
        # Masonry
        (r'(?:brick\s*work|block\s*work|masonry)', ScopeItemCategory.MASONRY,
         ["masonry", "brickwork", "blockwork"], QualityLevel.MINOR),
        # MEP
        (r'(?:electrical|plumbing|hvac|mep|mechanical)\s*(?:works?|system)?', ScopeItemCategory.MEP,
         ["mep", "electrical", "plumbing", "hvac"], QualityLevel.MAJOR),
        # Finishing
        (r'(?:flooring|painting|tiling|plastering|ceiling)', ScopeItemCategory.FINISHING,
         ["finishing", "flooring", "painting", "tiling"], QualityLevel.MINOR),
        # Landscaping
        (r'(?:landscaping|plantation|hardscape|softscape)', ScopeItemCategory.LANDSCAPING,
         ["landscaping", "hardscape", "softscape"], QualityLevel.MINOR),
    ]

    # Apply rules
    found_items = set()
    item_count = 0

    for pattern, category, keywords, priority in extraction_rules:
        matches = re.findall(pattern, text)
        if matches and str(matches[0]) not in found_items:
            item_count += 1
            found_items.add(str(matches[0]))

            # Try to extract context around the match
            match = re.search(pattern, text)
            if match:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = data.document_text[start:end].strip()
            else:
                context = ""

            scope_items.append(ScopeItem(
                id=f"SI-{item_count:03d}",
                description=f"{category.value.title()} works: {matches[0]}",
                category=category,
                keywords=keywords,
                priority=priority,
                confidence=0.7  # Lower confidence for rule-based
            ))

    # Extract categories found
    categories_found = list(set(item.category.value for item in scope_items))

    result = ScopeExtractionResult(
        project_name=data.project_name,
        project_type=data.project_type,
        scope_items=scope_items,
        summary=f"Rule-based extraction identified {len(scope_items)} scope items across {len(categories_found)} categories.",
        total_items=len(scope_items),
        categories_found=categories_found,
        extraction_confidence=0.7,
        warnings=["Used rule-based extraction - LLM unavailable. Results may be less accurate."]
    )

    print(f"[SCOPE EXTRACTOR] Rule-based extraction found {len(scope_items)} items")
    return result.model_dump()


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Test with sample document
    sample_scope = """
    PROJECT SCOPE OF WORK
    Project: ABC Commercial Complex
    Location: Mumbai, India

    1. CIVIL WORKS
    1.1 Site Development
    - Excavation: 5000 cu.m bulk excavation for basement
    - Earthwork: Filling and compaction as per IS 1200

    1.2 Foundation Works
    - Bored Cast-in-situ Piles: 250 nos, 600mm dia, 15m depth
    - Pile caps and grade beams as per structural drawings
    - Raft foundation for Tower B: 2500 sq.m

    2. STRUCTURAL WORKS
    2.1 RCC Superstructure
    - RCC columns, beams, and slabs as per IS 456:2000
    - Concrete grade: M40 for columns, M30 for slabs
    - Steel reinforcement: Fe500D grade

    2.2 Pre-cast Elements
    - Pre-cast facade panels for external cladding
    - Pre-cast staircase units

    3. WATERPROOFING
    - Basement waterproofing with membrane system
    - Terrace waterproofing with APP membrane
    - Toilet waterproofing with integral waterproofing compound

    4. MEP WORKS
    - Electrical installation as per IE Rules
    - Plumbing and sanitary installation
    - HVAC system for common areas
    """

    test_input = {
        "document_text": sample_scope,
        "document_type": "scope_of_work",
        "project_name": "ABC Commercial Complex",
        "project_type": "commercial"
    }

    result = extract_scope_items(test_input)
    print("\n" + "="*60)
    print("EXTRACTION RESULT")
    print("="*60)
    print(f"Project: {result['project_name']}")
    print(f"Total Items: {result['total_items']}")
    print(f"Categories: {result['categories_found']}")
    print("\nScope Items:")
    for item in result['scope_items'][:5]:
        print(f"  - [{item['category']}] {item['description']}")
