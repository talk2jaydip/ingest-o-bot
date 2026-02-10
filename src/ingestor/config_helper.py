"""
Shared configuration helper for index improvement scripts.

Provides environment-first configuration pattern matching build_index.py.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import Optional, List


# Load environment variables from .env file (searches up the directory tree)
# Capture whether a .env file was found/loaded for diagnostic output
# Locate and load .env; capture paths loaded for diagnostics
DOTENV_PATH = find_dotenv(raise_error_if_not_found=True)
DOTENV_PATHS = []
DOTENV_LOADED = False
if DOTENV_PATH:
    if load_dotenv(DOTENV_PATH):
        DOTENV_PATHS.append(DOTENV_PATH)
        DOTENV_LOADED = True


# Track where config values originate for diagnostics (CLI, env var name, fallback)
CONFIG_SOURCES = {}


def load_env_with_fallback(
    env_var: str,
    cli_arg=None,
    required=False,
    fallback_envs: Optional[List[str]] = None,
    default_value=None
):
    """
    Load configuration with environment-first pattern.

    Priority:
    1. Command-line argument (if provided)
    2. Primary environment variable
    3. Fallback environment variables (in order)
    4. Default value
    5. None (or error if required)

    Args:
        env_var: Primary environment variable name
        cli_arg: Command-line argument value (overrides env)
        required: Whether this value is required
        fallback_envs: List of fallback environment variable names
        default_value: Default value if not found

    Returns:
        Configuration value or None
    """
    # CLI arg overrides env var
    if cli_arg is not None:
        CONFIG_SOURCES[env_var] = "CLI"
        return cli_arg

    # Check environment primary name
    value = os.getenv(env_var)
    if value:
        CONFIG_SOURCES[env_var] = f"env:{env_var}"
        return value

    # If not found, check any provided fallback environment variable names
    if not value and fallback_envs:
        for alt in fallback_envs:
            alt_val = os.getenv(alt)
            if alt_val:
                value = alt_val
                CONFIG_SOURCES[env_var] = f"env:{alt}"
                break

    # Use default if no value found
    if not value and default_value is not None:
        value = default_value
        CONFIG_SOURCES[env_var] = "default"

    if not value:
        CONFIG_SOURCES[env_var] = "missing"

    if required and not value:
        raise ValueError(f"Required configuration missing: {env_var} (also checked: {fallback_envs})")

    return value


def get_azure_search_service(cli_arg=None, required=True) -> Optional[str]:
    """Get Azure Search service name from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_SEARCH_SERVICE",
        cli_arg,
        required=required,
        fallback_envs=["SEARCH_SERVICE_NAME", "AI_SEARCH_NAME_01"]
    )


def get_azure_search_key(cli_arg=None, required=False) -> Optional[str]:
    """Get Azure Search API key from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_SEARCH_KEY",
        cli_arg,
        required=required,
        fallback_envs=["AI_SEARCH_KEY_01"]
    )


def get_azure_search_index(cli_arg=None, required=True, default="myproject-index") -> Optional[str]:
    """Get Azure Search index name from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_SEARCH_INDEX",
        cli_arg,
        required=required,
        fallback_envs=["INDEX"],
        default_value=default
    )


def get_azure_openai_endpoint(cli_arg=None, required=False) -> Optional[str]:
    """Get Azure OpenAI endpoint from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_OPENAI_ENDPOINT",
        cli_arg,
        required=required,
        fallback_envs=["OPENAI_ACCOUNT_ENDPOINT_0", "OPENAI_ACCOUNT_ENDPOINT_1", "EMBEDDING_ENDPOINT"]
    )


def get_azure_openai_deployment(cli_arg=None, required=False) -> Optional[str]:
    """Get Azure OpenAI embedding deployment from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        cli_arg,
        required=required,
        fallback_envs=["AZURE_OPENAI_EMBEDDING_NAME", "AZURE_OPENAI_EMBEDDING_MODEL"]
    )


def get_azure_openai_key(cli_arg=None, required=False) -> Optional[str]:
    """Get Azure OpenAI API key from CLI or environment."""
    return load_env_with_fallback(
        "AZURE_OPENAI_KEY",
        cli_arg,
        required=required,
        fallback_envs=["OPENAI_ACCOUNT_KEY_0", "OPENAI_ACCOUNT_KEY_1", "EMBEDDING_KEY"]
    )


def print_config_diagnostic(error_msg: str = None):
    """Print diagnostic information for configuration troubleshooting."""
    print("\n[ERROR] Configuration Error:\n", file=sys.stderr)

    if error_msg:
        print(f"  Error: {error_msg}\n", file=sys.stderr)

    if DOTENV_PATHS:
        print("  .env files loaded:", file=sys.stderr)
        for p in DOTENV_PATHS:
            print(f"    - {p}", file=sys.stderr)
    else:
        print(f"  .env file found at: {DOTENV_PATH if DOTENV_PATH else '(not found)'}", file=sys.stderr)

    print(f"  .env loaded: {DOTENV_LOADED}", file=sys.stderr)

    print("  Values checked:", file=sys.stderr)
    env_vars = [
        "AZURE_SEARCH_SERVICE",
        "SEARCH_SERVICE_NAME",
        "AI_SEARCH_NAME_01",
        "AZURE_SEARCH_KEY",
        "AI_SEARCH_KEY_01",
        "AZURE_SEARCH_INDEX",
        "INDEX"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "API" in var:
                display_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"    {var}={display_value}", file=sys.stderr)
        else:
            print(f"    {var}={value}", file=sys.stderr)

    if CONFIG_SOURCES:
        print("\n  Configuration sources used:", file=sys.stderr)
        for key, source in CONFIG_SOURCES.items():
            print(f"    {key}: {source}", file=sys.stderr)

    print("\n  You can provide configuration via CLI arguments or set in your .env file.", file=sys.stderr)
    print("  Example .env entries:", file=sys.stderr)
    print("    AZURE_SEARCH_SERVICE=your-service-name", file=sys.stderr)
    print("    AZURE_SEARCH_KEY=your-admin-key", file=sys.stderr)
    print("    AZURE_SEARCH_INDEX=your-index-name\n", file=sys.stderr)
