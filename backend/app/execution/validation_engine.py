"""
JSON Schema Validation Engine

Provides full JSON Schema validation for:
- Input data validation
- Output data validation
- Type checking
- Range constraints
- Pattern matching
- Custom validation rules
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from jsonschema import validate, ValidationError, Draft7Validator
    from jsonschema.exceptions import SchemaError
except ImportError:
    raise ImportError(
        "jsonschema is required for validation. "
        "Install with: pip install jsonschema>=4.17.0"
    )

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity level of validation errors"""
    ERROR = "error"      # Hard errors that must be fixed
    WARNING = "warning"  # Soft warnings that should be reviewed
    INFO = "info"        # Informational messages


@dataclass
class ValidationIssue:
    """Single validation issue"""

    severity: ValidationSeverity
    path: str  # JSON path to the issue (e.g., "input.axial_load_dead")
    message: str
    schema_path: Optional[str] = None  # Path in schema that failed
    expected: Optional[Any] = None     # Expected value/type
    actual: Optional[Any] = None       # Actual value/type


@dataclass
class ValidationResult:
    """Result of validation"""

    valid: bool
    issues: List[ValidationIssue]

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def error_messages(self) -> List[str]:
        """Get error messages as strings"""
        return [i.message for i in self.errors]

    @property
    def warning_messages(self) -> List[str]:
        """Get warning messages as strings"""
        return [i.message for i in self.warnings]


class ValidationEngine:
    """
    JSON Schema validation engine with enhanced error reporting

    Features:
    - Full JSON Schema Draft 7 support
    - Type validation (string, number, boolean, object, array)
    - Numeric constraints (minimum, maximum, multipleOf)
    - String constraints (minLength, maxLength, pattern)
    - Array constraints (minItems, maxItems, uniqueItems)
    - Object constraints (required, additionalProperties)
    - Enum validation
    - Detailed error formatting
    """

    def __init__(self):
        """Initialize validation engine"""
        self.validation_cache: Dict[str, Draft7Validator] = {}

    def validate_input(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate input data against JSON Schema

        Args:
            data: Data to validate
            schema: JSON Schema definition
            strict: If True, treat all issues as errors. If False, some may be warnings.

        Returns:
            ValidationResult with issues

        Example schema:
            {
                "type": "object",
                "required": ["axial_load_dead"],
                "properties": {
                    "axial_load_dead": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 10000
                    },
                    "concrete_grade": {
                        "type": "string",
                        "enum": ["M20", "M25", "M30"]
                    }
                }
            }
        """
        logger.info("Validating input data against schema")
        return self._validate(data, schema, "input", strict)

    def validate_output(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        strict: bool = False
    ) -> ValidationResult:
        """
        Validate output data against JSON Schema

        Args:
            data: Data to validate
            schema: JSON Schema definition
            strict: If True, treat all issues as errors

        Returns:
            ValidationResult with issues
        """
        logger.info("Validating output data against schema")
        return self._validate(data, schema, "output", strict)

    def _validate(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        context: str,
        strict: bool
    ) -> ValidationResult:
        """
        Core validation logic

        Args:
            data: Data to validate
            schema: JSON Schema
            context: Context name for error messages
            strict: Strict mode flag

        Returns:
            ValidationResult
        """
        issues: List[ValidationIssue] = []

        try:
            # Validate schema itself first
            try:
                Draft7Validator.check_schema(schema)
            except SchemaError as e:
                logger.error(f"Invalid schema: {e}")
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    path=context,
                    message=f"Invalid JSON Schema: {str(e)}"
                ))
                return ValidationResult(valid=False, issues=issues)

            # Create validator
            validator = Draft7Validator(schema)

            # Collect all validation errors
            errors = list(validator.iter_errors(data))

            if errors:
                for error in errors:
                    issue = self._format_validation_error(error, context, strict)
                    issues.append(issue)

                logger.warning(f"Validation found {len(issues)} issues")
                return ValidationResult(valid=False, issues=issues)

            logger.info("✅ Validation passed")
            return ValidationResult(valid=True, issues=[])

        except Exception as e:
            logger.error(f"Validation exception: {e}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=context,
                message=f"Validation failed with exception: {str(e)}"
            ))
            return ValidationResult(valid=False, issues=issues)

    def _format_validation_error(
        self,
        error: ValidationError,
        context: str,
        strict: bool
    ) -> ValidationIssue:
        """
        Format a validation error into a user-friendly issue

        Args:
            error: ValidationError from jsonschema
            context: Context name
            strict: Strict mode flag

        Returns:
            ValidationIssue
        """
        # Build JSON path
        if error.path:
            path = f"{context}.{'.'.join(str(p) for p in error.path)}"
        else:
            path = context

        # Determine severity
        # In strict mode, everything is an error
        # In non-strict mode, some issues might be warnings (e.g., missing optional fields)
        severity = ValidationSeverity.ERROR
        if not strict and error.validator in ["additionalProperties", "minProperties"]:
            severity = ValidationSeverity.WARNING

        # Extract expected and actual values
        expected = error.schema.get(error.validator) if error.schema else None
        actual = error.instance

        # Format message based on error type
        message = self._format_error_message(error, path)

        return ValidationIssue(
            severity=severity,
            path=path,
            message=message,
            schema_path=".".join(str(p) for p in error.schema_path) if error.schema_path else None,
            expected=expected,
            actual=actual
        )

    def _format_error_message(self, error: ValidationError, path: str) -> str:
        """
        Format error message based on validation type

        Args:
            error: ValidationError
            path: JSON path

        Returns:
            Formatted error message
        """
        validator = error.validator
        message = error.message
        instance = error.instance

        # Type errors
        if validator == "type":
            expected_type = error.schema.get("type")
            actual_type = type(instance).__name__
            return f"{path}: Expected type '{expected_type}', got '{actual_type}'"

        # Required fields
        elif validator == "required":
            missing_field = error.message.split("'")[1] if "'" in error.message else "unknown"
            return f"{path}.{missing_field}: This field is required"

        # Numeric constraints
        elif validator == "minimum":
            minimum = error.schema.get("minimum")
            return f"{path}: Value {instance} is less than minimum {minimum}"

        elif validator == "maximum":
            maximum = error.schema.get("maximum")
            return f"{path}: Value {instance} exceeds maximum {maximum}"

        elif validator == "multipleOf":
            multiple = error.schema.get("multipleOf")
            return f"{path}: Value {instance} is not a multiple of {multiple}"

        # String constraints
        elif validator == "minLength":
            min_length = error.schema.get("minLength")
            return f"{path}: String length {len(instance)} is less than minimum {min_length}"

        elif validator == "maxLength":
            max_length = error.schema.get("maxLength")
            return f"{path}: String length {len(instance)} exceeds maximum {max_length}"

        elif validator == "pattern":
            pattern = error.schema.get("pattern")
            return f"{path}: Value '{instance}' does not match pattern '{pattern}'"

        # Enum validation
        elif validator == "enum":
            allowed = error.schema.get("enum")
            return f"{path}: Value '{instance}' is not one of allowed values: {allowed}"

        # Array constraints
        elif validator == "minItems":
            min_items = error.schema.get("minItems")
            return f"{path}: Array has {len(instance)} items, minimum is {min_items}"

        elif validator == "maxItems":
            max_items = error.schema.get("maxItems")
            return f"{path}: Array has {len(instance)} items, maximum is {max_items}"

        elif validator == "uniqueItems":
            return f"{path}: Array contains duplicate items"

        # Object constraints
        elif validator == "additionalProperties":
            # Extract the additional property name from the error path
            if error.path:
                extra_prop = error.path[-1]
                return f"{path}: Additional property '{extra_prop}' is not allowed"
            return f"{path}: Contains additional properties that are not allowed"

        # Default: use original message
        else:
            return f"{path}: {message}"

    def validate_custom_rules(
        self,
        data: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate data against custom validation rules

        Custom rules format:
            [
                {
                    "rule": "range_check",
                    "field": "axial_load_dead",
                    "min": 0,
                    "max": 10000,
                    "message": "Axial load must be between 0 and 10000 kN"
                },
                {
                    "rule": "dependency",
                    "field": "steel_grade",
                    "depends_on": "concrete_grade",
                    "message": "Steel grade requires concrete grade"
                }
            ]

        Args:
            data: Data to validate
            rules: List of custom validation rules

        Returns:
            ValidationResult
        """
        issues: List[ValidationIssue] = []

        for rule in rules:
            rule_type = rule.get("rule")

            if rule_type == "range_check":
                issue = self._validate_range_rule(data, rule)
            elif rule_type == "dependency":
                issue = self._validate_dependency_rule(data, rule)
            elif rule_type == "expression":
                issue = self._validate_expression_rule(data, rule)
            else:
                logger.warning(f"Unknown rule type: {rule_type}")
                continue

            if issue:
                issues.append(issue)

        valid = all(i.severity != ValidationSeverity.ERROR for i in issues)
        return ValidationResult(valid=valid, issues=issues)

    def _validate_range_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Validate range check rule"""
        field = rule.get("field")
        min_val = rule.get("min")
        max_val = rule.get("max")
        message = rule.get("message", f"{field} out of range")

        value = data.get(field)
        if value is None:
            return None  # Field not present, skip

        if min_val is not None and value < min_val:
            return ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=field,
                message=message,
                expected=f">= {min_val}",
                actual=value
            )

        if max_val is not None and value > max_val:
            return ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=field,
                message=message,
                expected=f"<= {max_val}",
                actual=value
            )

        return None

    def _validate_dependency_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Validate field dependency rule"""
        field = rule.get("field")
        depends_on = rule.get("depends_on")
        message = rule.get("message", f"{field} requires {depends_on}")

        # If field is present, dependency must also be present
        if field in data and depends_on not in data:
            return ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=field,
                message=message
            )

        return None

    def _validate_expression_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Validate expression rule (e.g., "field_a > field_b")"""
        expression = rule.get("expression")
        message = rule.get("message", f"Expression failed: {expression}")

        # Simple expression evaluation
        # For security, we don't use eval() - instead support basic comparisons
        try:
            # TODO: Implement safe expression evaluation
            # For now, just log and skip
            logger.warning(f"Expression rules not yet implemented: {expression}")
            return None
        except Exception as e:
            return ValidationIssue(
                severity=ValidationSeverity.WARNING,
                path="expression",
                message=f"Could not evaluate expression: {str(e)}"
            )


# Convenience functions for quick validation
def validate_input_data(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
    """
    Quick validation of input data

    Args:
        data: Input data
        schema: JSON Schema

    Returns:
        ValidationResult
    """
    engine = ValidationEngine()
    return engine.validate_input(data, schema)


def validate_output_data(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
    """
    Quick validation of output data

    Args:
        data: Output data
        schema: JSON Schema

    Returns:
        ValidationResult
    """
    engine = ValidationEngine()
    return engine.validate_output(data, schema)
