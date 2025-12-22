"""
Phase 2 Sprint 1: THE MATH ENGINE
Engine Registry - Dynamic Function Lookup

This module provides the registry system for dynamically invoking calculation functions
by name. This enables the Configuration over Code philosophy where workflow schemas
can reference functions without hardcoding logic.

Registry Structure:
    {
        "tool_name": {
            "function_name": callable,
            "description": str,
            "input_schema": dict,
            "output_schema": dict
        }
    }

Usage:
    >>> from app.engines.registry import engine_registry
    >>> func = engine_registry.get_function("civil_foundation_designer_v1", "design_isolated_footing")
    >>> result = func(input_data)
"""

from typing import Dict, Any, Callable, Optional
from pydantic import BaseModel
import inspect


# ============================================================================
# REGISTRY CLASS
# ============================================================================

class EngineRegistry:
    """
    Central registry for all calculation engine functions.

    This enables dynamic function invocation based on workflow schemas stored
    in the database (Phase 2 Sprint 2+).
    """

    def __init__(self):
        """Initialize empty registry."""
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        tool_name: str,
        function_name: str,
        function: Callable,
        description: str = "",
        input_schema: Optional[type] = None,
        output_schema: Optional[type] = None
    ) -> None:
        """
        Register a calculation function under a tool name.

        Args:
            tool_name: Name of the tool (e.g., "civil_foundation_designer_v1")
            function_name: Name of the function (e.g., "design_isolated_footing")
            function: The callable function
            description: Human-readable description
            input_schema: Pydantic model for input validation (optional)
            output_schema: Pydantic model for output validation (optional)

        Example:
            >>> registry = EngineRegistry()
            >>> registry.register_tool(
            ...     "civil_foundation_designer_v1",
            ...     "design_isolated_footing",
            ...     design_isolated_footing,
            ...     "Design isolated RCC footing per IS 456:2000"
            ... )
        """
        if tool_name not in self._registry:
            self._registry[tool_name] = {}

        self._registry[tool_name][function_name] = {
            "function": function,
            "description": description,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "signature": str(inspect.signature(function))
        }

    def get_function(self, tool_name: str, function_name: str) -> Optional[Callable]:
        """
        Retrieve a registered function.

        Args:
            tool_name: Tool name
            function_name: Function name

        Returns:
            The callable function, or None if not found

        Example:
            >>> func = registry.get_function("civil_foundation_designer_v1", "design_isolated_footing")
            >>> result = func(input_data)
        """
        if tool_name in self._registry and function_name in self._registry[tool_name]:
            return self._registry[tool_name][function_name]["function"]
        return None

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about all functions in a tool.

        Args:
            tool_name: Tool name

        Returns:
            Dictionary of function info, or None if tool not found
        """
        return self._registry.get(tool_name)

    def list_tools(self) -> list[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._registry.keys())

    def list_functions(self, tool_name: str) -> list[str]:
        """
        List all functions for a given tool.

        Args:
            tool_name: Tool name

        Returns:
            List of function names, or empty list if tool not found
        """
        if tool_name in self._registry:
            return list(self._registry[tool_name].keys())
        return []

    def invoke(
        self,
        tool_name: str,
        function_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a registered function with input data.

        Args:
            tool_name: Tool name
            function_name: Function name
            input_data: Input dictionary

        Returns:
            Output dictionary from function

        Raises:
            ValueError: If tool or function not found
            Exception: Any exception raised by the function

        Example:
            >>> result = registry.invoke(
            ...     "civil_foundation_designer_v1",
            ...     "design_isolated_footing",
            ...     {"axial_load_dead": 600, ...}
            ... )
        """
        func = self.get_function(tool_name, function_name)

        if func is None:
            raise ValueError(
                f"Function '{function_name}' not found in tool '{tool_name}'. "
                f"Available tools: {self.list_tools()}"
            )

        # Invoke function
        result = func(input_data)

        return result

    def get_registry_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the entire registry.

        Returns:
            Dictionary with tool counts and function lists
        """
        summary = {
            "total_tools": len(self._registry),
            "tools": {}
        }

        for tool_name, functions in self._registry.items():
            summary["tools"][tool_name] = {
                "function_count": len(functions),
                "functions": [
                    {
                        "name": func_name,
                        "description": func_info["description"],
                        "signature": func_info["signature"]
                    }
                    for func_name, func_info in functions.items()
                ]
            }

        return summary


# ============================================================================
# GLOBAL REGISTRY INSTANCE
# ============================================================================

# Create global registry instance
engine_registry = EngineRegistry()


# ============================================================================
# REGISTER ALL FUNCTIONS (Phase 2 Sprint 1)
# ============================================================================

def register_all_engines():
    """
    Register all available calculation engine functions.

    This function is called at application startup to populate the registry.
    As new engines are added in future sprints, they should be registered here.
    """
    # ========================================================================
    # CIVIL FOUNDATION DESIGN (Phase 2 Sprint 1)
    # ========================================================================
    from app.engines.foundation.design_isolated_footing import (
        design_isolated_footing,
        FoundationInput,
        InitialDesignData
    )
    from app.engines.foundation.optimize_schedule import (
        optimize_schedule,
        FinalDesignData
    )

    # Register civil_foundation_designer_v1 tool
    engine_registry.register_tool(
        tool_name="civil_foundation_designer_v1",
        function_name="design_isolated_footing",
        function=design_isolated_footing,
        description="Design isolated RCC footing following IS 456:2000. "
                    "Calculates dimensions, reinforcement, and performs code checks.",
        input_schema=FoundationInput,
        output_schema=InitialDesignData
    )

    engine_registry.register_tool(
        tool_name="civil_foundation_designer_v1",
        function_name="optimize_schedule",
        function=optimize_schedule,
        description="Optimize foundation design, standardize dimensions, "
                    "generate bar bending schedule and material quantities.",
        input_schema=InitialDesignData,
        output_schema=FinalDesignData
    )

    # ========================================================================
    # STRUCTURAL BEAM DESIGN (Phase 3 Sprint 3)
    # ========================================================================
    from app.engines.structural.beam_designer import (
        analyze_beam,
        design_beam_reinforcement,
        BeamInput,
        BeamAnalysisResult,
        BeamDesignOutput
    )

    engine_registry.register_tool(
        tool_name="structural_beam_designer_v1",
        function_name="analyze_beam",
        function=analyze_beam,
        description="Analyze RCC beam for bending moments and shear forces. "
                    "Step 1 of beam design following IS 456:2000.",
        input_schema=BeamInput,
        output_schema=None  # Returns analysis dict
    )

    engine_registry.register_tool(
        tool_name="structural_beam_designer_v1",
        function_name="design_beam_reinforcement",
        function=design_beam_reinforcement,
        description="Design flexural and shear reinforcement for RCC beam. "
                    "Step 2 of beam design following IS 456:2000.",
        input_schema=None,  # Takes analysis dict
        output_schema=BeamDesignOutput
    )

    # ========================================================================
    # STRUCTURAL STEEL COLUMN DESIGN (Phase 3 Sprint 3)
    # ========================================================================
    from app.engines.structural.steel_column_designer import (
        check_column_capacity,
        design_column_connection,
        SteelColumnInput,
        SteelColumnOutput
    )

    engine_registry.register_tool(
        tool_name="structural_steel_column_designer_v1",
        function_name="check_column_capacity",
        function=check_column_capacity,
        description="Check steel column capacity for axial loads. "
                    "Includes section selection, slenderness, and buckling checks per IS 800:2007.",
        input_schema=SteelColumnInput,
        output_schema=None  # Returns capacity dict
    )

    engine_registry.register_tool(
        tool_name="structural_steel_column_designer_v1",
        function_name="design_column_connection",
        function=design_column_connection,
        description="Design column base plate and connections. "
                    "Includes anchor bolts, welds, and material quantities.",
        input_schema=None,  # Takes capacity dict
        output_schema=SteelColumnOutput
    )

    # ========================================================================
    # STRUCTURAL SLAB DESIGN (Phase 3 Sprint 3)
    # ========================================================================
    from app.engines.structural.slab_designer import (
        analyze_slab,
        design_slab_reinforcement,
        SlabInput,
        SlabDesignOutput
    )

    engine_registry.register_tool(
        tool_name="structural_slab_designer_v1",
        function_name="analyze_slab",
        function=analyze_slab,
        description="Analyze RCC slab (one-way or two-way) for bending moments. "
                    "Step 1 of slab design following IS 456:2000.",
        input_schema=SlabInput,
        output_schema=None  # Returns analysis dict
    )

    engine_registry.register_tool(
        tool_name="structural_slab_designer_v1",
        function_name="design_slab_reinforcement",
        function=design_slab_reinforcement,
        description="Design reinforcement for RCC slab including deflection check. "
                    "Step 2 of slab design following IS 456:2000.",
        input_schema=None,  # Takes analysis dict
        output_schema=SlabDesignOutput
    )

    # ========================================================================
    # CIVIL COMBINED FOOTING DESIGN (Phase 3 Sprint 3 - Extended)
    # ========================================================================
    from app.engines.civil.combined_footing_designer import (
        analyze_combined_footing,
        design_combined_footing_reinforcement,
    )

    engine_registry.register_tool(
        tool_name="civil_combined_footing_designer_v1",
        function_name="analyze_combined_footing",
        function=analyze_combined_footing,
        description="Analyze combined footing for multiple columns. "
                    "Calculates dimensions, load distribution, and stability per IS 456:2000.",
        input_schema=None,
        output_schema=None
    )

    engine_registry.register_tool(
        tool_name="civil_combined_footing_designer_v1",
        function_name="design_combined_footing_reinforcement",
        function=design_combined_footing_reinforcement,
        description="Design reinforcement for combined footing including punching shear check. "
                    "Step 2 of combined footing design following IS 456:2000.",
        input_schema=None,
        output_schema=None
    )

    # ========================================================================
    # CIVIL RETAINING WALL DESIGN (Phase 3 Sprint 3 - Extended)
    # ========================================================================
    from app.engines.civil.retaining_wall_designer import (
        analyze_retaining_wall,
        design_retaining_wall_reinforcement,
    )

    engine_registry.register_tool(
        tool_name="civil_retaining_wall_designer_v1",
        function_name="analyze_retaining_wall",
        function=analyze_retaining_wall,
        description="Analyze cantilever retaining wall for stability. "
                    "Checks overturning, sliding, and bearing per IS 14458.",
        input_schema=None,
        output_schema=None
    )

    engine_registry.register_tool(
        tool_name="civil_retaining_wall_designer_v1",
        function_name="design_retaining_wall_reinforcement",
        function=design_retaining_wall_reinforcement,
        description="Design reinforcement for retaining wall stem and base. "
                    "Step 2 of retaining wall design following IS 456:2000.",
        input_schema=None,
        output_schema=None
    )

    # ========================================================================
    # STRUCTURAL BASE PLATE & ANCHOR BOLT DESIGN (Phase 3 Sprint 3 - Extended)
    # ========================================================================
    from app.engines.structural.base_plate_designer import (
        analyze_base_plate,
        design_anchor_bolts,
    )

    engine_registry.register_tool(
        tool_name="structural_base_plate_designer_v1",
        function_name="analyze_base_plate",
        function=analyze_base_plate,
        description="Analyze steel column base plate requirements. "
                    "Calculates plate dimensions and bearing check per IS 800:2007.",
        input_schema=None,
        output_schema=None
    )

    engine_registry.register_tool(
        tool_name="structural_base_plate_designer_v1",
        function_name="design_anchor_bolts",
        function=design_anchor_bolts,
        description="Design anchor bolts and connection details for base plate. "
                    "Includes embedment, weld design, and layout per IS 800:2007.",
        input_schema=None,
        output_schema=None
    )

    # ========================================================================
    # ARCHITECTURAL ROOM DATA SHEET GENERATOR (Phase 3 Sprint 3 - Extended)
    # ========================================================================
    from app.engines.architectural.room_data_sheet_generator import (
        analyze_room_requirements,
        generate_room_data_sheet,
    )

    engine_registry.register_tool(
        tool_name="architectural_rds_generator_v1",
        function_name="analyze_room_requirements",
        function=analyze_room_requirements,
        description="Analyze room requirements based on type and dimensions. "
                    "Step 1 of Room Data Sheet generation following NBC 2016.",
        input_schema=None,
        output_schema=None
    )

    engine_registry.register_tool(
        tool_name="architectural_rds_generator_v1",
        function_name="generate_room_data_sheet",
        function=generate_room_data_sheet,
        description="Generate complete Room Data Sheet with finishes, MEP, and FF&E. "
                    "Step 2 of RDS generation following standard documentation practices.",
        input_schema=None,
        output_schema=None
    )

    # ========================================================================
    # CONSTRUCTABILITY AGENT (Phase 4 Sprint 2)
    # ========================================================================
    from app.engines.constructability.rebar_congestion import (
        analyze_rebar_congestion,
        RebarCongestionInput,
        RebarCongestionResult,
    )
    from app.engines.constructability.formwork_complexity import (
        analyze_formwork_complexity,
        FormworkComplexityInput,
        FormworkComplexityResult,
    )
    from app.engines.constructability.constructability_analyzer import (
        analyze_constructability,
        generate_red_flag_report,
        generate_constructability_plan,
        ConstructabilityAnalysisInput,
        ConstructabilityAnalysisResult,
        RedFlagReport,
        ConstructabilityPlan,
    )

    # Rebar congestion analysis
    engine_registry.register_tool(
        tool_name="structural_constructability_analyzer_v1",
        function_name="analyze_rebar_congestion",
        function=analyze_rebar_congestion,
        description="Analyze rebar congestion in structural members. "
                    "Checks reinforcement ratio and clear spacing per IS 456:2000.",
        input_schema=RebarCongestionInput,
        output_schema=RebarCongestionResult
    )

    # Formwork complexity analysis
    engine_registry.register_tool(
        tool_name="structural_constructability_analyzer_v1",
        function_name="analyze_formwork_complexity",
        function=analyze_formwork_complexity,
        description="Analyze formwork complexity for structural members. "
                    "Evaluates dimension standardization and custom requirements.",
        input_schema=FormworkComplexityInput,
        output_schema=FormworkComplexityResult
    )

    # Comprehensive constructability analysis
    engine_registry.register_tool(
        tool_name="structural_constructability_analyzer_v1",
        function_name="analyze_constructability",
        function=analyze_constructability,
        description="Comprehensive constructability analysis combining rebar congestion, "
                    "formwork complexity, access constraints, and sequencing evaluation.",
        input_schema=ConstructabilityAnalysisInput,
        output_schema=ConstructabilityAnalysisResult
    )

    # Red Flag Report generation
    engine_registry.register_tool(
        tool_name="structural_constructability_analyzer_v1",
        function_name="generate_red_flag_report",
        function=generate_red_flag_report,
        description="Generate Red Flag Report from constructability analysis results. "
                    "Executive summary of critical issues requiring attention.",
        input_schema=None,  # Takes analysis result dict
        output_schema=RedFlagReport
    )

    # Constructability plan generation
    engine_registry.register_tool(
        tool_name="structural_constructability_analyzer_v1",
        function_name="generate_constructability_plan",
        function=generate_constructability_plan,
        description="Generate constructability mitigation plan with strategies. "
                    "Creates actionable steps to address identified issues.",
        input_schema=None,  # Takes analysis result dict
        output_schema=ConstructabilityPlan
    )

    # Future registrations will go here:
    # - mep_hvac_designer_v1
    # - mep_electrical_designer_v1
    # - etc.


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tool_names() -> list[str]:
    """Get list of all registered tool names."""
    return engine_registry.list_tools()


def get_function_names(tool_name: str) -> list[str]:
    """Get list of function names for a tool."""
    return engine_registry.list_functions(tool_name)


def invoke_engine(
    tool_name: str,
    function_name: str,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to invoke an engine function.

    Args:
        tool_name: Tool name
        function_name: Function name
        input_data: Input dictionary

    Returns:
        Output dictionary
    """
    return engine_registry.invoke(tool_name, function_name, input_data)


def print_registry_summary():
    """Print a formatted summary of the registry."""
    summary = engine_registry.get_registry_summary()

    print(f"\n{'='*70}")
    print(f"ENGINE REGISTRY SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tools: {summary['total_tools']}\n")

    for tool_name, tool_info in summary['tools'].items():
        print(f"Tool: {tool_name}")
        print(f"  Functions: {tool_info['function_count']}")

        for func in tool_info['functions']:
            print(f"\n  • {func['name']}")
            print(f"    Description: {func['description']}")
            print(f"    Signature: {func['signature']}")

        print()

    print(f"{'='*70}\n")


# ============================================================================
# INITIALIZATION
# ============================================================================

# Auto-register all engines when module is imported
# This ensures the registry is always ready to use
register_all_engines()


if __name__ == "__main__":
    # Print registry summary when run directly
    print_registry_summary()
