"""
CSA AIaaS Platform - Application Configuration
Sprint 1: The Neuro-Skeleton

Central configuration management for the application.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.

    All configuration is centralized here for maintainability.
    """

    # Database Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # LLM Configuration (OpenRouter)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")

    # Application Configuration
    APP_NAME: str = "CSA AIaaS Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # LangGraph Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))

    # Risk Thresholds
    HIGH_RISK_THRESHOLD: float = float(os.getenv("HIGH_RISK_THRESHOLD", "0.7"))
    MEDIUM_RISK_THRESHOLD: float = float(os.getenv("MEDIUM_RISK_THRESHOLD", "0.4"))

    @classmethod
    def validate(cls, require_database: bool = False) -> bool:
        """
        Validate that all required settings are present.

        Args:
            require_database: If True, Supabase credentials are required.
                             If False, only warns about missing database.

        Returns:
            True if all required settings are present

        Raises:
            ValueError: If required settings are missing
        """
        errors = []
        warnings = []

        # Database validation (optional for testing)
        if not cls.SUPABASE_URL or not cls.SUPABASE_ANON_KEY:
            if require_database:
                errors.append("SUPABASE_URL and SUPABASE_ANON_KEY are required")
            else:
                warnings.append("Supabase not configured - audit logging will be disabled")

        # LLM validation (always required)
        if not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is required")

        # Print warnings
        if warnings:
            print("⚠ Configuration warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        # Raise errors if any
        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return True


# Create global settings instance
settings = Settings()
