"""Apply performance optimizations to .env file."""
import re
from pathlib import Path

def update_env_value(content, key, new_value):
    """Update or add an environment variable."""
    pattern = rf'^{key}=.*$'
    replacement = f'{key}={new_value}'

    if re.search(pattern, content, re.MULTILINE):
        # Update existing
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        print(f"  [OK] Updated: {key}={new_value}")
    else:
        # Add new (after performance section if exists)
        if '# PERFORMANCE OPTIMIZATION' in content:
            content = content.replace(
                '# PERFORMANCE OPTIMIZATION FOR 100+ FILES\n',
                f'# PERFORMANCE OPTIMIZATION FOR 100+ FILES\n{replacement}\n'
            )
        else:
            # Add at end
            content += f'\n# Performance Optimization\n{replacement}\n'
        print(f"  [OK] Added: {key}={new_value}")

    return content

def apply_optimizations(level='standard'):
    """Apply performance optimizations to .env file.

    Args:
        level: 'standard' (8x parallel) or 'aggressive' (16x parallel)
    """
    env_path = Path('.env')

    if not env_path.exists():
        print("ERROR: .env file not found")
        return False

    # Read current .env with UTF-8 encoding
    content = env_path.read_text(encoding='utf-8')

    # Create backup
    backup_path = Path('.env.backup')
    backup_path.write_text(content, encoding='utf-8')
    print(f"[OK] Backup created: {backup_path}")

    print("\nApplying optimizations:")
    print("=" * 60)

    # Apply optimizations based on level
    if level == 'standard':
        print("\nLevel: STANDARD (Safe for most setups)")
        content = update_env_value(content, 'AZURE_MAX_WORKERS', '8')
        content = update_env_value(content, 'AZURE_OPENAI_MAX_CONCURRENCY', '15')
        content = update_env_value(content, 'AZURE_EMBED_BATCH_SIZE', '256')
        content = update_env_value(content, 'AZURE_UPLOAD_BATCH_SIZE', '500')

        print("\nExpected improvement: 2-3x faster")
        print("100 files: 86 min → ~30 min")

    elif level == 'aggressive':
        print("\nLevel: AGGRESSIVE (Requires high quotas)")
        content = update_env_value(content, 'AZURE_MAX_WORKERS', '16')
        content = update_env_value(content, 'AZURE_OPENAI_MAX_CONCURRENCY', '20')
        content = update_env_value(content, 'AZURE_DI_MAX_CONCURRENCY', '5')
        content = update_env_value(content, 'AZURE_EMBED_BATCH_SIZE', '256')
        content = update_env_value(content, 'AZURE_UPLOAD_BATCH_SIZE', '500')

        print("\nExpected improvement: 4-5x faster")
        print("100 files: 86 min → ~17 min")
        print("\nWARNING: May hit rate limits!")

    # Write updated .env with UTF-8 encoding
    env_path.write_text(content, encoding='utf-8')
    print("\n" + "=" * 60)
    print(f"[OK] Updated: {env_path}")

    print("\nNext steps:")
    print("  1. Test with a small batch: python -m ingestor.cli")
    print("  2. Monitor logs for rate limit errors")
    print("  3. Adjust settings if needed")
    print("  4. To revert: mv .env.backup .env")

    return True

if __name__ == "__main__":
    import sys

    level = sys.argv[1] if len(sys.argv) > 1 else 'standard'

    if level not in ['standard', 'aggressive']:
        print("Usage: python apply_performance_optimizations.py [standard|aggressive]")
        print("\nLevels:")
        print("  standard   - 8x parallel, safe for most setups (2-3x faster)")
        print("  aggressive - 16x parallel, requires high quotas (4-5x faster)")
        sys.exit(1)

    apply_optimizations(level)
