-- ============================================================================
-- Migration 001: Add Persona Support to Workflow Steps
-- Part 8 Enhancement: Dynamic Schema & Workflow Extensibility
-- ============================================================================
--
-- This migration adds persona support to workflow steps as specified in Part 8.
-- Personas allow different AI contexts for different step types:
-- - Designer: Focus on initial design and sizing
-- - Engineer: Focus on detailed calculations and optimization
-- - Checker: Focus on validation and verification
-- - Coordinator: Focus on cross-discipline coordination
--
-- Note: The persona field is stored within the workflow_steps JSONB column,
-- not as a separate database column. This migration updates existing workflows
-- to include the default persona value.
--
-- ============================================================================

-- Update existing workflow_steps to include default persona
-- This is a data migration, not a schema migration
UPDATE csa.deliverable_schemas
SET workflow_steps = (
    SELECT jsonb_agg(
        CASE
            WHEN elem ? 'persona' THEN elem
            ELSE jsonb_set(elem, '{persona}', '"general"'::jsonb)
        END
    )
    FROM jsonb_array_elements(workflow_steps) elem
)
WHERE id IN (
    SELECT id FROM csa.deliverable_schemas
);

-- Add comment documenting the persona field
COMMENT ON COLUMN csa.deliverable_schemas.workflow_steps IS
'JSONB array defining the sequence of calculation steps. Each step includes:
- step_number: Sequence order
- step_name: Unique identifier
- description: Human-readable description
- persona: AI context (Designer, Engineer, Checker, Coordinator, general)
- function_to_call: Engine function reference
- input_mapping: Variable substitution mapping
- output_variable: Result storage variable
- error_handling: Retry and failure behavior
- timeout_seconds: Maximum execution time';

-- Verify the update
SELECT
    deliverable_type,
    jsonb_pretty(workflow_steps) as updated_workflow_steps
FROM csa.deliverable_schemas;

-- ============================================================================
-- Example: Adding a new workflow with persona support
-- ============================================================================
/*
INSERT INTO csa.deliverable_schemas (
    deliverable_type,
    display_name,
    discipline,
    workflow_steps,
    input_schema
) VALUES (
    'beam_design',
    'Steel Beam Design (IS 800)',
    'structural',
    '[
        {
            "step_number": 1,
            "step_name": "initial_sizing",
            "description": "Initial beam sizing based on span and loading",
            "persona": "Designer",
            "function_to_call": "structural_beam_designer_v1.size_beam",
            "input_mapping": {
                "span": "$input.span",
                "load": "$input.load"
            },
            "output_variable": "beam_size"
        },
        {
            "step_number": 2,
            "step_name": "detailed_design",
            "description": "Detailed design and member checks",
            "persona": "Engineer",
            "function_to_call": "structural_beam_designer_v1.detail_design",
            "input_mapping": {
                "beam_size": "$step1.beam_size",
                "loading": "$input.loading"
            },
            "output_variable": "detailed_design"
        },
        {
            "step_number": 3,
            "step_name": "verification",
            "description": "Verify design against IS 800 requirements",
            "persona": "Checker",
            "function_to_call": "structural_beam_designer_v1.verify_design",
            "input_mapping": {
                "design": "$step2.detailed_design"
            },
            "output_variable": "verification_result"
        }
    ]'::jsonb,
    '{"type": "object", "required": ["span", "load"]}'::jsonb
);
*/

-- ============================================================================
-- Rollback (if needed)
-- ============================================================================
/*
-- Remove persona field from all workflows
UPDATE csa.deliverable_schemas
SET workflow_steps = (
    SELECT jsonb_agg(elem - 'persona')
    FROM jsonb_array_elements(workflow_steps) elem
);
*/
