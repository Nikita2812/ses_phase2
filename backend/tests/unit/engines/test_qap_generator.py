"""
Phase 4 Sprint 4: Unit Tests for QAP Generator

Tests for:
- Scope extraction
- ITP mapping
- QAP assembly
- Full pipeline generation
"""

import pytest
from typing import Dict, Any

from app.engines.qap import (
    # Functions
    extract_scope_items,
    map_scope_to_itps,
    assemble_qap,
    generate_qap,
    validate_scope_document,
    list_available_itps,
    get_template_by_id,
    get_templates_by_category,
    list_all_itp_ids,
    # Models
    ScopeItem,
    ScopeItemCategory,
    ScopeExtractionInput,
    ScopeExtractionResult,
    ITPMappingInput,
    ITPMappingResult,
    QAPDocument,
    QualityLevel,
    InspectionType,
)


# =============================================================================
# TEST DATA
# =============================================================================

SAMPLE_SCOPE_DOCUMENT = """
PROJECT SCOPE OF WORK
Project: Test Commercial Complex
Location: Mumbai, India

1. CIVIL WORKS
1.1 Site Development
- Bulk excavation: 5000 cu.m
- Filling and compaction as per IS 1200

1.2 Foundation Works
- Bored Cast-in-situ Piles: 250 nos, 600mm dia, 15m depth
- Pile caps and grade beams
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

MINIMAL_SCOPE = "Project includes piling works and RCC construction."

EMPTY_SCOPE = ""


# =============================================================================
# SCOPE EXTRACTION TESTS
# =============================================================================

class TestScopeExtraction:
    """Tests for scope extraction functionality."""

    def test_extract_scope_items_basic(self):
        """Test basic scope extraction from a document."""
        input_data = {
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work",
            "project_name": "Test Project",
            "project_type": "commercial"
        }

        result = extract_scope_items(input_data)

        # Verify structure
        assert "scope_items" in result
        assert "total_items" in result
        assert "categories_found" in result
        assert "extraction_confidence" in result

        # Should extract multiple items
        assert result["total_items"] > 0
        assert len(result["scope_items"]) > 0

    def test_extract_scope_items_minimal(self):
        """Test extraction with minimal document."""
        input_data = {
            "document_text": MINIMAL_SCOPE,
            "document_type": "scope_of_work"
        }

        result = extract_scope_items(input_data)

        # Should still extract something
        assert result["total_items"] >= 0
        # Even if LLM fails, rule-based should work
        assert "scope_items" in result

    def test_extract_scope_items_categories(self):
        """Test that correct categories are identified."""
        input_data = {
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work"
        }

        result = extract_scope_items(input_data)

        # Should find multiple categories
        categories = result.get("categories_found", [])
        assert len(categories) > 0

    def test_scope_extraction_input_validation(self):
        """Test input validation for scope extraction."""
        # Valid input
        valid_input = ScopeExtractionInput(
            document_text="Sample scope",
            document_type="scope_of_work"
        )
        assert valid_input.document_text == "Sample scope"

        # Test default values
        assert valid_input.extract_quantities is True
        assert valid_input.extract_locations is True


# =============================================================================
# ITP MAPPING TESTS
# =============================================================================

class TestITPMapping:
    """Tests for ITP mapping functionality."""

    def test_map_scope_to_itps_basic(self):
        """Test basic ITP mapping."""
        # First extract scope items
        extraction = extract_scope_items({
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work"
        })

        # Then map to ITPs
        mapping_input = {
            "scope_items": extraction["scope_items"],
            "quality_level": "major"
        }

        result = map_scope_to_itps(mapping_input)

        assert "mappings" in result
        assert "total_itps_mapped" in result
        assert "coverage_percentage" in result
        assert result["total_scope_items"] > 0

    def test_map_scope_to_itps_with_piling(self):
        """Test ITP mapping for piling scope items."""
        scope_items = [
            ScopeItem(
                id="SI-001",
                description="Bored cast-in-situ piling - 600mm diameter",
                category=ScopeItemCategory.PILING,
                keywords=["bored pile", "piling", "foundation"],
                priority=QualityLevel.CRITICAL
            ).model_dump()
        ]

        result = map_scope_to_itps({
            "scope_items": scope_items,
            "quality_level": "critical"
        })

        # Should find piling ITP
        assert result["total_itps_mapped"] > 0
        itp_ids = [m["itp_id"] for m in result["mappings"]]
        assert any("PIL" in itp_id for itp_id in itp_ids)

    def test_map_scope_to_itps_with_concrete(self):
        """Test ITP mapping for concrete scope items."""
        scope_items = [
            ScopeItem(
                id="SI-002",
                description="RCC columns and beams",
                category=ScopeItemCategory.CONCRETE,
                keywords=["rcc", "concrete", "column", "beam"],
                priority=QualityLevel.CRITICAL
            ).model_dump()
        ]

        result = map_scope_to_itps({
            "scope_items": scope_items,
            "quality_level": "major"
        })

        # Should find concrete ITP
        assert result["total_itps_mapped"] > 0
        itp_ids = [m["itp_id"] for m in result["mappings"]]
        assert any("CON" in itp_id for itp_id in itp_ids)

    def test_map_scope_with_optional_itps(self):
        """Test ITP mapping with optional ITPs included."""
        scope_items = [
            ScopeItem(
                id="SI-001",
                description="Structural steel fabrication",
                category=ScopeItemCategory.STEEL,
                keywords=["steel", "fabrication"],
                priority=QualityLevel.MAJOR
            ).model_dump()
        ]

        result = map_scope_to_itps({
            "scope_items": scope_items,
            "include_optional": True
        })

        assert "mappings" in result

    def test_coverage_percentage_calculation(self):
        """Test coverage percentage is calculated correctly."""
        scope_items = [
            ScopeItem(
                id="SI-001",
                description="Piling works",
                category=ScopeItemCategory.PILING,
                keywords=["pile"],
                priority=QualityLevel.MAJOR
            ).model_dump(),
            ScopeItem(
                id="SI-002",
                description="Concrete works",
                category=ScopeItemCategory.CONCRETE,
                keywords=["concrete"],
                priority=QualityLevel.MAJOR
            ).model_dump()
        ]

        result = map_scope_to_itps({"scope_items": scope_items})

        # Coverage should be between 0 and 100
        assert 0 <= result["coverage_percentage"] <= 100


# =============================================================================
# ITP TEMPLATES TESTS
# =============================================================================

class TestITPTemplates:
    """Tests for ITP template functions."""

    def test_list_all_itp_ids(self):
        """Test listing all ITP template IDs."""
        itp_ids = list_all_itp_ids()

        assert isinstance(itp_ids, list)
        assert len(itp_ids) > 0
        assert all(isinstance(id, str) for id in itp_ids)

    def test_get_template_by_id(self):
        """Test getting a specific ITP template."""
        # Get first available ID
        itp_ids = list_all_itp_ids()
        template = get_template_by_id(itp_ids[0])

        assert template is not None
        assert hasattr(template, "itp_id")
        assert hasattr(template, "itp_name")
        assert hasattr(template, "checkpoints")

    def test_get_templates_by_category(self):
        """Test getting templates by category."""
        piling_templates = get_templates_by_category(ScopeItemCategory.PILING)

        assert isinstance(piling_templates, list)
        # Should have at least one piling ITP
        assert len(piling_templates) > 0
        assert all(t.category == ScopeItemCategory.PILING for t in piling_templates)

    def test_list_available_itps(self):
        """Test listing available ITPs with summary."""
        result = list_available_itps()

        assert "total_templates" in result
        assert "categories" in result
        assert result["total_templates"] > 0

    def test_template_has_checkpoints(self):
        """Test that templates have checkpoints defined."""
        itp_ids = list_all_itp_ids()
        template = get_template_by_id(itp_ids[0])

        assert len(template.checkpoints) > 0
        checkpoint = template.checkpoints[0]
        assert hasattr(checkpoint, "checkpoint_id")
        assert hasattr(checkpoint, "activity")
        assert hasattr(checkpoint, "inspection_type")
        assert hasattr(checkpoint, "acceptance_criteria")


# =============================================================================
# QAP ASSEMBLY TESTS
# =============================================================================

class TestQAPAssembly:
    """Tests for QAP document assembly."""

    def test_assemble_qap_basic(self):
        """Test basic QAP assembly."""
        # Extract and map first
        extraction = extract_scope_items({
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work",
            "project_name": "Test Project"
        })

        mapping = map_scope_to_itps({
            "scope_items": extraction["scope_items"]
        })

        # Assemble QAP
        result = assemble_qap({
            "project_name": "Test Project",
            "project_number": "PRJ-001",
            "scope_extraction": extraction,
            "itp_mapping": mapping
        })

        assert "qap_id" in result
        assert "document_number" in result
        assert "chapters" in result
        assert "project_itps" in result

    def test_assemble_qap_with_forms(self):
        """Test QAP assembly includes inspection forms."""
        extraction = extract_scope_items({
            "document_text": MINIMAL_SCOPE,
            "document_type": "scope_of_work"
        })

        mapping = map_scope_to_itps({
            "scope_items": extraction["scope_items"]
        })

        result = assemble_qap({
            "project_name": "Test",
            "scope_extraction": extraction,
            "itp_mapping": mapping,
            "include_forms": True
        })

        assert "inspection_forms" in result

    def test_assemble_qap_chapters(self):
        """Test that QAP has proper chapter structure."""
        extraction = extract_scope_items({
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work"
        })

        mapping = map_scope_to_itps({
            "scope_items": extraction["scope_items"]
        })

        result = assemble_qap({
            "project_name": "Test",
            "scope_extraction": extraction,
            "itp_mapping": mapping
        })

        chapters = result.get("chapters", [])
        assert len(chapters) > 0

        # Check chapter structure
        for chapter in chapters:
            assert "chapter_number" in chapter
            assert "title" in chapter
            assert "sections" in chapter

    def test_assemble_qap_reference_standards(self):
        """Test that reference standards are collected."""
        extraction = extract_scope_items({
            "document_text": SAMPLE_SCOPE_DOCUMENT,
            "document_type": "scope_of_work"
        })

        mapping = map_scope_to_itps({
            "scope_items": extraction["scope_items"]
        })

        result = assemble_qap({
            "project_name": "Test",
            "scope_extraction": extraction,
            "itp_mapping": mapping
        })

        assert "reference_standards" in result
        assert isinstance(result["reference_standards"], list)


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    """Tests for complete QAP generation pipeline."""

    def test_generate_qap_complete(self):
        """Test complete QAP generation."""
        result = generate_qap({
            "scope_document": SAMPLE_SCOPE_DOCUMENT,
            "project_name": "Test Commercial Complex",
            "project_number": "PRJ-2024-001",
            "client_name": "Test Client",
            "contractor_name": "Test Contractor",
            "output_format": "json"
        })

        assert result["success"] is True
        assert result["qap_id"] is not None
        assert result["scope_items_found"] > 0
        assert result["coverage_percentage"] >= 0

    def test_generate_qap_with_text_output(self):
        """Test QAP generation with text output."""
        result = generate_qap({
            "scope_document": SAMPLE_SCOPE_DOCUMENT,
            "project_name": "Test Project",
            "output_format": "text"
        })

        assert result["success"] is True
        assert result["qap_text"] is not None
        assert "QUALITY ASSURANCE PLAN" in result["qap_text"]

    def test_generate_qap_with_both_outputs(self):
        """Test QAP generation with both JSON and text output."""
        result = generate_qap({
            "scope_document": SAMPLE_SCOPE_DOCUMENT,
            "project_name": "Test Project",
            "output_format": "both"
        })

        assert result["success"] is True
        assert result["qap_document"] is not None
        assert result["qap_text"] is not None

    def test_generate_qap_processing_time(self):
        """Test that processing time is recorded."""
        result = generate_qap({
            "scope_document": MINIMAL_SCOPE,
            "project_name": "Test"
        })

        assert "processing_time_ms" in result
        assert result["processing_time_ms"] > 0


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidation:
    """Tests for document validation."""

    def test_validate_document_valid(self):
        """Test validation of a valid document."""
        result = validate_scope_document(SAMPLE_SCOPE_DOCUMENT)

        assert result["is_valid"] is True
        assert result["document_length"] > 0
        assert len(result["construction_terms_found"]) > 0

    def test_validate_document_short(self):
        """Test validation of a short document."""
        result = validate_scope_document("Short")

        assert result["is_valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_document_no_construction_terms(self):
        """Test validation of document without construction terms."""
        result = validate_scope_document("This is a long document about something completely unrelated to construction and building works.")

        # May still be valid but should have suggestions
        assert "suggestions" in result


# =============================================================================
# MODEL TESTS
# =============================================================================

class TestModels:
    """Tests for Pydantic models."""

    def test_scope_item_model(self):
        """Test ScopeItem model."""
        item = ScopeItem(
            id="SI-001",
            description="Test scope item",
            category=ScopeItemCategory.PILING,
            keywords=["pile", "foundation"],
            priority=QualityLevel.CRITICAL
        )

        assert item.id == "SI-001"
        assert item.category == ScopeItemCategory.PILING
        assert item.priority == QualityLevel.CRITICAL
        assert item.confidence == 1.0  # Default

    def test_scope_item_category_enum(self):
        """Test ScopeItemCategory enum values."""
        assert ScopeItemCategory.PILING.value == "piling"
        assert ScopeItemCategory.CONCRETE.value == "concrete"
        assert ScopeItemCategory.STEEL.value == "steel"

    def test_quality_level_enum(self):
        """Test QualityLevel enum values."""
        assert QualityLevel.CRITICAL.value == "critical"
        assert QualityLevel.MAJOR.value == "major"
        assert QualityLevel.MINOR.value == "minor"

    def test_inspection_type_enum(self):
        """Test InspectionType enum values."""
        assert InspectionType.HOLD.value == "hold"
        assert InspectionType.WITNESS.value == "witness"
        assert InspectionType.REVIEW.value == "review"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_extract_empty_document(self):
        """Test extraction with empty document."""
        result = extract_scope_items({
            "document_text": "",
            "document_type": "scope_of_work"
        })

        # Should not crash, may return empty or have warnings
        assert "scope_items" in result

    def test_map_empty_scope_items(self):
        """Test mapping with empty scope items."""
        result = map_scope_to_itps({
            "scope_items": []
        })

        assert result["total_scope_items"] == 0
        assert result["coverage_percentage"] == 0

    def test_invalid_itp_id(self):
        """Test getting non-existent ITP template."""
        template = get_template_by_id("NON_EXISTENT_ID")
        assert template is None


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
