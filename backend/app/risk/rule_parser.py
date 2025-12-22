"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Risk Rule Parser

This module provides a specialized parser for risk rules that extends the
base condition evaluator with risk-specific features.

Features:
- Variable resolution from workflow context
- Risk assessment context ($assessment.*)
- Safe evaluation with error handling
- Performance metrics tracking
"""

import re
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from app.execution.condition_parser import ConditionEvaluator, SimpleConditionEvaluator

logger = logging.getLogger(__name__)


@dataclass
class ParsedVariable:
    """Represents a parsed variable reference."""
    full_path: str  # e.g., "$input.load"
    source: str  # e.g., "input", "step1", "context", "assessment"
    path: List[str]  # e.g., ["load"] or ["initial_design_data", "footing_depth"]


@dataclass
class RuleParseResult:
    """Result of parsing a rule condition."""
    is_valid: bool
    error_message: Optional[str] = None
    variables: List[ParsedVariable] = None
    required_steps: Set[int] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.required_steps is None:
            self.required_steps = set()


@dataclass
class RuleEvalResult:
    """Result of evaluating a rule."""
    success: bool
    result: bool = False
    error_message: Optional[str] = None
    evaluation_time_ms: int = 0
    variables_resolved: Dict[str, Any] = None

    def __post_init__(self):
        if self.variables_resolved is None:
            self.variables_resolved = {}


class RiskRuleParser:
    """
    Parser for risk rule conditions.

    Supports:
    - Standard workflow variables: $input.*, $step*.*, $context.*
    - Risk assessment variables: $assessment.technical_risk, $assessment.safety_risk, etc.
    - Complex boolean expressions: AND, OR, NOT
    - Ternary-like expressions for counting: (cond1 ? 1 : 0) + (cond2 ? 1 : 0)

    Thread-safe and cacheable.
    """

    # Pattern for extracting variable references
    VARIABLE_PATTERN = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)')

    # Pattern for step references
    STEP_PATTERN = re.compile(r'\$step(\d+)')

    # Pattern for ternary-like expressions
    TERNARY_PATTERN = re.compile(r'\(([^?]+)\s*\?\s*(\d+)\s*:\s*(\d+)\)')

    def __init__(self, use_advanced_parser: bool = True):
        """
        Initialize rule parser.

        Args:
            use_advanced_parser: Use pyparsing-based evaluator (default True)
        """
        self.use_advanced_parser = use_advanced_parser
        if use_advanced_parser:
            try:
                self._evaluator = ConditionEvaluator()
            except ImportError:
                logger.warning("pyparsing not available, falling back to simple evaluator")
                self._evaluator = None
                self.use_advanced_parser = False
        else:
            self._evaluator = None

    def parse(self, condition: str) -> RuleParseResult:
        """
        Parse a rule condition and validate syntax.

        Args:
            condition: Condition expression to parse

        Returns:
            RuleParseResult with validation status and extracted info
        """
        if not condition or not condition.strip():
            return RuleParseResult(
                is_valid=False,
                error_message="Condition cannot be empty"
            )

        try:
            # Extract all variable references
            variables = self._extract_variables(condition)

            # Find required step numbers
            required_steps = self._find_required_steps(condition)

            # Try to parse with evaluator to validate syntax
            if self.use_advanced_parser and self._evaluator:
                try:
                    self._evaluator.parse(condition)
                except Exception as e:
                    return RuleParseResult(
                        is_valid=False,
                        error_message=f"Syntax error: {str(e)}",
                        variables=variables,
                        required_steps=required_steps
                    )

            return RuleParseResult(
                is_valid=True,
                variables=variables,
                required_steps=required_steps
            )

        except Exception as e:
            logger.error(f"Parse error for condition '{condition}': {e}")
            return RuleParseResult(
                is_valid=False,
                error_message=str(e)
            )

    def evaluate(
        self,
        condition: str,
        context: Dict[str, Any],
        assessment: Optional[Dict[str, Any]] = None
    ) -> RuleEvalResult:
        """
        Evaluate a rule condition against execution context.

        Args:
            condition: Condition expression to evaluate
            context: Workflow execution context with input, steps, context
            assessment: Optional risk assessment data

        Returns:
            RuleEvalResult with evaluation result and metrics
        """
        start_time = time.perf_counter()

        if not condition or not condition.strip():
            return RuleEvalResult(
                success=True,
                result=True,  # Empty condition is always true
                evaluation_time_ms=0
            )

        try:
            # Build extended context with assessment data
            extended_context = self._build_extended_context(context, assessment)

            # Handle ternary expressions first (preprocessing)
            processed_condition = self._preprocess_ternary(condition, extended_context)

            # Evaluate using appropriate evaluator
            if self.use_advanced_parser and self._evaluator:
                result = self._evaluator.evaluate(processed_condition, extended_context)
            else:
                result = SimpleConditionEvaluator.evaluate(processed_condition, extended_context)

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Track resolved variables for debugging
            variables_resolved = self._resolve_all_variables(condition, extended_context)

            return RuleEvalResult(
                success=True,
                result=bool(result),
                evaluation_time_ms=elapsed_ms,
                variables_resolved=variables_resolved
            )

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Evaluation error for '{condition}': {e}")
            return RuleEvalResult(
                success=False,
                result=False,
                error_message=str(e),
                evaluation_time_ms=elapsed_ms
            )

    def validate_condition(
        self,
        condition: str,
        test_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], Optional[bool]]:
        """
        Validate a condition and optionally test it.

        Args:
            condition: Condition to validate
            test_context: Optional context for test evaluation

        Returns:
            Tuple of (is_valid, error_message, test_result)
        """
        parse_result = self.parse(condition)

        if not parse_result.is_valid:
            return False, parse_result.error_message, None

        if test_context:
            eval_result = self.evaluate(condition, test_context)
            if not eval_result.success:
                return False, eval_result.error_message, None
            return True, None, eval_result.result

        return True, None, None

    def get_required_variables(self, condition: str) -> List[str]:
        """
        Get list of variable paths required by a condition.

        Args:
            condition: Condition expression

        Returns:
            List of variable paths (e.g., ["$input.load", "$step1.data.value"])
        """
        variables = self._extract_variables(condition)
        return [v.full_path for v in variables]

    def can_evaluate_at_step(self, condition: str, completed_steps: Set[int]) -> bool:
        """
        Check if a condition can be evaluated given completed steps.

        Args:
            condition: Condition expression
            completed_steps: Set of step numbers that have completed

        Returns:
            True if all required steps are complete
        """
        required = self._find_required_steps(condition)
        return required.issubset(completed_steps)

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _extract_variables(self, condition: str) -> List[ParsedVariable]:
        """Extract all variable references from condition."""
        variables = []
        matches = self.VARIABLE_PATTERN.findall(condition)

        for match in matches:
            full_path = f"${match}"
            parts = match.split(".")
            source = parts[0]
            path = parts[1:] if len(parts) > 1 else []

            variables.append(ParsedVariable(
                full_path=full_path,
                source=source,
                path=path
            ))

        return variables

    def _find_required_steps(self, condition: str) -> Set[int]:
        """Find step numbers referenced in condition."""
        matches = self.STEP_PATTERN.findall(condition)
        return {int(m) for m in matches}

    def _build_extended_context(
        self,
        context: Dict[str, Any],
        assessment: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build extended context including assessment data."""
        extended = dict(context)

        if assessment:
            # Add assessment as a top-level source
            extended["assessment"] = assessment
            # Also add to steps for backward compatibility
            if "steps" not in extended:
                extended["steps"] = {}
            extended["steps"]["assessment"] = assessment

        return extended

    def _preprocess_ternary(self, condition: str, context: Dict[str, Any]) -> str:
        """
        Preprocess ternary-like expressions.

        Converts: (condition ? 1 : 0) -> 1 or 0 based on evaluation
        Used for counting triggered conditions.
        """
        def replace_ternary(match):
            inner_condition = match.group(1).strip()
            true_val = int(match.group(2))
            false_val = int(match.group(3))

            try:
                if self.use_advanced_parser and self._evaluator:
                    result = self._evaluator.evaluate(inner_condition, context)
                else:
                    result = SimpleConditionEvaluator.evaluate(inner_condition, context)
                return str(true_val if result else false_val)
            except Exception:
                # If evaluation fails, return false_val
                return str(false_val)

        processed = self.TERNARY_PATTERN.sub(replace_ternary, condition)
        return processed

    def _resolve_all_variables(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve all variables in condition for debugging."""
        resolved = {}
        variables = self._extract_variables(condition)

        for var in variables:
            try:
                value = self._resolve_variable(var, context)
                resolved[var.full_path] = value
            except Exception as e:
                resolved[var.full_path] = f"<error: {e}>"

        return resolved

    def _resolve_variable(
        self,
        var: ParsedVariable,
        context: Dict[str, Any]
    ) -> Any:
        """Resolve a single variable reference."""
        source = var.source
        path = var.path

        # Get source data
        if source == "input":
            data = context.get("input", {})
        elif source == "context":
            data = context.get("context", {})
        elif source == "assessment":
            data = context.get("assessment", {})
            if not data:
                data = context.get("steps", {}).get("assessment", {})
        elif source.startswith("step"):
            steps_data = context.get("steps", {})
            if path:
                var_name = path[0]
                path = path[1:]
                data = steps_data.get(var_name, {})
            else:
                raise ValueError(f"Step reference must include variable: {var.full_path}")
        else:
            raise ValueError(f"Unknown variable source: {source}")

        # Traverse path
        for key in path:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                raise ValueError(f"Cannot access key '{key}' on {type(data)}")

        return data


# Singleton instance for convenience
_parser_instance: Optional[RiskRuleParser] = None


def get_rule_parser() -> RiskRuleParser:
    """Get singleton rule parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = RiskRuleParser()
    return _parser_instance


def evaluate_risk_condition(
    condition: str,
    context: Dict[str, Any],
    assessment: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, int]:
    """
    Convenience function to evaluate a risk condition.

    Args:
        condition: Condition expression
        context: Workflow context
        assessment: Optional risk assessment data

    Returns:
        Tuple of (result, error_message or "", evaluation_time_ms)
    """
    parser = get_rule_parser()
    result = parser.evaluate(condition, context, assessment)

    return (
        result.result if result.success else False,
        result.error_message or "",
        result.evaluation_time_ms
    )
