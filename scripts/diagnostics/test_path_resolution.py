#!/usr/bin/env python3
"""Test path resolution fix"""
from pathlib import Path
import os

# Simulate running from src directory
os.chdir("/c/Work/ingest-o-bot/src")
print(f"Current directory: {os.getcwd()}")

# User provides this relative path
user_path = r".\envs\.env.azure-local-input.example"
print(f"\nUser provided path: {user_path}")

# Old behavior (without .resolve())
old_path = Path(user_path)
print(f"\nOld behavior (without .resolve()):")
print(f"  Path object: {old_path}")
print(f"  Exists: {old_path.exists()}")

# New behavior (with .resolve())
new_path = Path(user_path).resolve()
print(f"\nNew behavior (with .resolve()):")
print(f"  Resolved path: {new_path}")
print(f"  Exists: {new_path.exists()}")

# Show what the correct path should be
correct_path = Path("/c/Work/ingest-o-bot/envs/.env.azure-local-input.example")
print(f"\nCorrect path (from root):")
print(f"  Path: {correct_path}")
print(f"  Exists: {correct_path.exists()}")

# Test with correct relative path from src
correct_relative = Path("../envs/.env.azure-local-input.example").resolve()
print(f"\nCorrect relative path from src:")
print(f"  Path: {correct_relative}")
print(f"  Exists: {correct_relative.exists()}")
