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
    # Import foundation design functions
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

    # Future registrations will go here:
    # - structural_steel_designer_v1
    # - architectural_layout_generator_v1
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
