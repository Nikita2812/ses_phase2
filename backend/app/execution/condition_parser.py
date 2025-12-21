"""
Advanced Conditional Expression Parser

Supports complex boolean expressions with:
- Logical operators: AND, OR, NOT
- Comparison operators: ==, !=, <, >, <=, >=, IN, NOT IN
- Variable references: $input.field, $stepN.variable, $context.key
- Parentheses for grouping
- Type-safe evaluation
"""

import re
import logging
from typing import Any, Dict, List, Union
from enum import Enum

try:
    from pyparsing import (
        Word, alphas, alphanums, nums, oneOf, infixNotation, opAssoc,
        Suppress, Literal, QuotedString, pyparsing_common, ParserElement,
        ParseException, CaselessKeyword
    )
except ImportError:
    raise ImportError(
        "pyparsing is required for advanced conditional expressions. "
        "Install with: pip install pyparsing>=3.0.9"
    )

logger = logging.getLogger(__name__)

# Enable packrat parsing for better performance
ParserElement.enablePackrat()


class ComparisonOp(str, Enum):
    """Comparison operators"""
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    IN = "IN"
    NOT_IN = "NOT IN"


class LogicalOp(str, Enum):
    """Logical operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class ConditionEvaluator:
    """
    Evaluates complex conditional expressions

    Supports:
    - "$input.value > 100 AND $step1.design_ok == true"
    - "$input.discipline IN ['civil', 'structural']"
    - "NOT ($step2.risk_score >= 0.9 OR $input.override == true)"
    - "($input.load > 1000 OR $input.force > 500) AND $step1.design_ok == true"
    """

    def __init__(self):
        """Initialize parser with grammar definition"""
        self.grammar = self._build_grammar()

    def _build_grammar(self):
        """
        Build pyparsing grammar for conditional expressions

        Grammar:
            expression := logical_expr
            logical_expr := comparison_expr ((AND | OR) comparison_expr)*
            comparison_expr := NOT? (value op value | (expression))
            value := variable | number | string | boolean | list
            variable := $word(.word)*
            op := == | != | < | > | <= | >= | IN | NOT IN
        """
        # Basic literals
        number = pyparsing_common.number()
        string = QuotedString("'") | QuotedString('"')
        boolean = (
            CaselessKeyword("true") | CaselessKeyword("false") |
            CaselessKeyword("True") | CaselessKeyword("False")
        )

        # Variable reference: $input.field, $step1.variable, $context.key
        variable_name = Word(alphas + "_", alphanums + "_")
        variable = Suppress("$") + variable_name + \
            (Suppress(".") + variable_name)[...] # Allow nested: $step1.data.value

        # List literal: ['a', 'b', 'c'] or [1, 2, 3]
        list_element = string | number
        list_expr = Suppress("[") + list_element + \
            (Suppress(",") + list_element)[...] + Suppress("]")

        # Value can be variable, number, string, boolean, or list
        value = variable | list_expr | number | string | boolean

        # Comparison operators
        comparison_op = (
            Literal("==") | Literal("!=") |
            Literal("<=") | Literal(">=") |  # Must come before < and >
            Literal("<") | Literal(">") |
            CaselessKeyword("NOT IN") | CaselessKeyword("IN")
        )

        # Comparison expression: value op value
        comparison = value + comparison_op + value

        # Logical expression with precedence:
        # 1. NOT (highest precedence, right-associative)
        # 2. AND (medium precedence, left-associative)
        # 3. OR (lowest precedence, left-associative)
        expression = infixNotation(
            comparison,
            [
                (CaselessKeyword("NOT"), 1, opAssoc.RIGHT),
                (CaselessKeyword("AND"), 2, opAssoc.LEFT),
                (CaselessKeyword("OR"), 2, opAssoc.LEFT),
            ]
        )

        return expression

    def parse(self, condition: str) -> List:
        """
        Parse condition string into abstract syntax tree

        Args:
            condition: Condition string to parse

        Returns:
            Parsed AST (nested list structure)

        Raises:
            ParseException: If condition has syntax errors
        """
        try:
            logger.debug(f"Parsing condition: {condition}")
            result = self.grammar.parseString(condition, parseAll=True)
            logger.debug(f"Parsed AST: {result.asList()}")
            return result.asList()
        except ParseException as e:
            logger.error(f"Parse error: {e}")
            raise ValueError(f"Invalid condition syntax: {str(e)}")

    def evaluate(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Parse and evaluate condition against context

        Args:
            condition: Condition string to evaluate
            context: Execution context with variables

        Returns:
            Boolean result of evaluation

        Raises:
            ValueError: If condition is invalid or variables not found
        """
        if not condition or not condition.strip():
            # Empty condition is always true
            return True

        try:
            ast = self.parse(condition)
            result = self._evaluate_node(ast[0], context)
            logger.info(f"Condition '{condition}' evaluated to {result}")
            return result
        except Exception as e:
            logger.error(f"Evaluation error for '{condition}': {e}")
            raise

    def _evaluate_node(self, node: Union[List, str, float, int, bool], context: Dict[str, Any]) -> Any:
        """
        Recursively evaluate AST node

        Args:
            node: AST node (can be list, literal, or operator)
            context: Execution context

        Returns:
            Evaluated value
        """
        # Literal values
        if isinstance(node, (int, float)):
            return node
        elif isinstance(node, str):
            if node.lower() in ["true", "false"]:
                return node.lower() == "true"
            # Could be a string literal or variable - context will determine
            return node

        # Must be a list (operator with operands)
        if not isinstance(node, list):
            raise ValueError(f"Unexpected node type: {type(node)}")

        # Check for logical operators
        if len(node) == 2 and str(node[0]).upper() == "NOT":
            # NOT operator (unary)
            return not self._evaluate_node(node[1], context)

        elif len(node) == 3:
            left = node[0]
            op = str(node[1]).upper()
            right = node[2]

            # Logical operators
            if op == "AND":
                left_val = self._evaluate_node(left, context)
                if not left_val:
                    return False  # Short-circuit
                return self._evaluate_node(right, context)

            elif op == "OR":
                left_val = self._evaluate_node(left, context)
                if left_val:
                    return True  # Short-circuit
                return self._evaluate_node(right, context)

            # Comparison operators
            else:
                return self._evaluate_comparison(left, op, right, context)

        else:
            raise ValueError(f"Unexpected node structure: {node}")

    def _evaluate_comparison(
        self,
        left: Any,
        op: str,
        right: Any,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate comparison expression

        Args:
            left: Left operand (can be variable reference or literal)
            op: Comparison operator
            right: Right operand (can be variable reference or literal)
            context: Execution context

        Returns:
            Boolean result of comparison
        """
        # Resolve values (variables or literals)
        left_val = self._resolve_value(left, context)
        right_val = self._resolve_value(right, context)

        logger.debug(f"Comparing: {left_val} {op} {right_val}")

        # Type checking for numeric comparisons
        if op in ["<", ">", "<=", ">="]:
            if not (isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))):
                raise TypeError(
                    f"Cannot compare {type(left_val).__name__} and {type(right_val).__name__} with {op}"
                )

        # Perform comparison
        try:
            if op == "==":
                return left_val == right_val
            elif op == "!=":
                return left_val != right_val
            elif op == "<":
                return left_val < right_val
            elif op == ">":
                return left_val > right_val
            elif op == "<=":
                return left_val <= right_val
            elif op == ">=":
                return left_val >= right_val
            elif op == "IN":
                return left_val in right_val
            elif op == "NOT IN":
                return left_val not in right_val
            else:
                raise ValueError(f"Unsupported operator: {op}")
        except Exception as e:
            raise ValueError(f"Comparison failed: {left_val} {op} {right_val} - {str(e)}")

    def _resolve_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """
        Resolve a value (variable reference or literal)

        Args:
            value: Value to resolve (can be variable reference or literal)
            context: Execution context

        Returns:
            Resolved value
        """
        # Already a literal number or boolean
        if isinstance(value, (int, float, bool)):
            return value

        # String could be literal or variable reference
        if isinstance(value, str):
            # Boolean strings
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"
            # Otherwise treat as string literal
            return value

        # List of tokens (variable reference or list literal)
        if isinstance(value, list):
            # Check if it's a variable reference
            if len(value) >= 2 and isinstance(value[0], str):
                # Variable reference: ['input', 'field'] or ['step1', 'data', 'value']
                return self._resolve_variable(value, context)
            else:
                # List literal
                return [self._resolve_value(v, context) for v in value]

        raise ValueError(f"Cannot resolve value: {value} (type: {type(value)})")

    def _resolve_variable(self, var_path: List[str], context: Dict[str, Any]) -> Any:
        """
        Resolve variable reference from context

        Args:
            var_path: Variable path components (e.g., ['input', 'field'] for $input.field)
            context: Execution context with 'input', 'steps', 'context' keys

        Returns:
            Resolved variable value

        Raises:
            ValueError: If variable not found
        """
        if not var_path:
            raise ValueError("Empty variable path")

        source = var_path[0]
        path = var_path[1:]

        logger.debug(f"Resolving variable: ${'.'.join(var_path)}")

        # Get source data
        if source == "input":
            data = context.get("input", {})
        elif source == "context":
            data = context.get("context", {})
        elif source.startswith("step"):
            # Extract step number: step1 -> 1
            match = re.match(r"step(\d+)", source)
            if not match:
                raise ValueError(f"Invalid step reference: {source}")

            step_num = int(match.group(1))

            # Get step data from context
            steps_data = context.get("steps", {})

            # Find the output variable for this step
            # Context structure: {"steps": {"output_var_name": {...}, ...}}
            # We need to find which output_var belongs to step_num

            # For now, assume direct access by step number
            # This requires the context to be structured with step numbers
            if not path:
                raise ValueError(f"Step reference must include output variable: $step{step_num}.variable")

            var_name = path[0]
            path = path[1:]

            if var_name not in steps_data:
                raise ValueError(f"Step output variable '{var_name}' not found. Available: {list(steps_data.keys())}")

            data = steps_data[var_name]
        else:
            raise ValueError(f"Unknown variable source: {source}")

        # Traverse nested path
        for key in path:
            if isinstance(data, dict):
                if key not in data:
                    raise ValueError(f"Variable key '{key}' not found in {data.keys()}")
                data = data[key]
            else:
                raise ValueError(f"Cannot access key '{key}' on non-dict value: {type(data)}")

        logger.debug(f"Resolved ${'.'.join(var_path)} = {data}")
        return data


# Simple regex-based fallback for basic conditions (backward compatibility)
class SimpleConditionEvaluator:
    """
    Simple condition evaluator for basic comparisons (Sprint 2 compatibility)

    Supports:
    - $input.value > 100
    - $step1.design_ok == true
    - $input.discipline == "civil"

    Does NOT support:
    - Logical operators (AND, OR, NOT)
    - Parentheses
    - Complex expressions
    """

    COMPARISON_PATTERN = re.compile(
        r'(\$[\w.]+)\s*(==|!=|<|>|<=|>=)\s*(.+)'
    )

    @staticmethod
    def evaluate(condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate simple condition

        Args:
            condition: Simple condition string
            context: Execution context

        Returns:
            Boolean result

        Raises:
            ValueError: If condition format is invalid
        """
        if not condition or not condition.strip():
            return True

        match = SimpleConditionEvaluator.COMPARISON_PATTERN.match(condition.strip())
        if not match:
            raise ValueError(f"Invalid condition format: {condition}")

        variable_ref = match.group(1)
        operator = match.group(2)
        right_value_str = match.group(3).strip()

        # Resolve left side (variable)
        left_value = SimpleConditionEvaluator._resolve_variable(variable_ref, context)

        # Parse right side (literal)
        right_value = SimpleConditionEvaluator._parse_literal(right_value_str)

        # Perform comparison
        return SimpleConditionEvaluator._compare(left_value, operator, right_value)

    @staticmethod
    def _resolve_variable(var_ref: str, context: Dict[str, Any]) -> Any:
        """Resolve variable reference (Sprint 2 style)"""
        # Remove $ prefix
        var_path = var_ref[1:].split(".")
        source = var_path[0]
        path = var_path[1:]

        if source == "input":
            data = context.get("input", {})
        elif source == "context":
            data = context.get("context", {})
        elif source.startswith("step"):
            if not path:
                raise ValueError(f"Step reference must include variable: {var_ref}")
            var_name = path[0]
            path = path[1:]
            steps_data = context.get("steps", {})
            data = steps_data.get(var_name, {})
        else:
            raise ValueError(f"Unknown variable source: {source}")

        for key in path:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                raise ValueError(f"Cannot access key '{key}' on {type(data)}")

        return data

    @staticmethod
    def _parse_literal(value_str: str) -> Any:
        """Parse literal value from string"""
        value_str = value_str.strip()

        # Boolean
        if value_str.lower() in ["true", "false"]:
            return value_str.lower() == "true"

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # String (remove quotes if present)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        return value_str

    @staticmethod
    def _compare(left: Any, op: str, right: Any) -> bool:
        """Perform comparison"""
        if op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "<=":
            return left <= right
        elif op == ">=":
            return left >= right
        else:
            raise ValueError(f"Unsupported operator: {op}")
