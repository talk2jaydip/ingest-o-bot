#!/usr/bin/env python
"""End-to-end test for Gradio UI."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("GRADIO UI - END-TO-END TEST")
print("="*80)
print()

# Test 1: Check Gradio version
print("Test 1: Checking Gradio version...")
try:
    import gradio as gr
    print(f"✅ Gradio version: {gr.__version__}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 2: Import gradio_app
print("\nTest 2: Importing gradio_app module...")
try:
    import gradio_app
    print(f"✅ Module imported successfully")
    print(f"   - ENV_HELP_DATA: {len(gradio_app.ENV_HELP_DATA)} variables documented")
    print(f"   - SCENARIO_TEMPLATES: {len(gradio_app.SCENARIO_TEMPLATES)} scenarios")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 3: Test environment status
print("\nTest 3: Testing environment status...")
try:
    status = gradio_app.get_env_status()
    required_count = sum(1 for v in status.values() if v['required'] and v['set'])
    optional_count = sum(1 for v in status.values() if not v['required'] and v['set'])
    missing_required = sum(1 for v in status.values() if v['required'] and not v['set'])
    
    print(f"✅ Environment status working")
    print(f"   - Required variables set: {required_count}")
    print(f"   - Optional variables set: {optional_count}")
    print(f"   - Missing required: {missing_required}")
    
    if missing_required > 0:
        print(f"   ⚠️  Warning: {missing_required} required variables not set")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 4: Test help system
print("\nTest 4: Testing help system...")
try:
    help_html = gradio_app.generate_env_help_html()
    status_html = gradio_app.generate_env_status_html()
    print(f"✅ Help system working")
    print(f"   - Help HTML length: {len(help_html)} chars")
    print(f"   - Status HTML length: {len(status_html)} chars")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 5: Test UI creation
print("\nTest 5: Creating UI instance...")
try:
    demo = gradio_app.create_ui()
    print(f"✅ UI created successfully")
    print(f"   - Type: {type(demo).__name__}")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test scenario templates
print("\nTest 6: Testing scenario templates...")
try:
    for scenario_name, template in gradio_app.SCENARIO_TEMPLATES.items():
        assert 'description' in template
        assert 'notes' in template
    print(f"✅ All scenario templates valid")
    print(f"   Available scenarios:")
    for name in gradio_app.SCENARIO_TEMPLATES.keys():
        print(f"   - {name}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 7: Test masking function
print("\nTest 7: Testing credential masking...")
try:
    test_key = "ffa403f9943f4c19a09c686e38d507f8"
    masked = gradio_app.mask_sensitive_value(test_key)
    assert masked == "ffa403f9...********"
    print(f"✅ Masking working correctly")
    print(f"   Original: {test_key}")
    print(f"   Masked: {masked}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print()
print("="*80)
print("✅ ALL TESTS PASSED!")
print("="*80)
print()
print("The Gradio UI is ready to use!")
print()
print("To launch:")
print("  Windows: launch_ui.bat")
print("  Linux/Mac: ./launch_ui.sh")
print("  Direct: python gradio_app.py")
print()
print("Access: http://localhost:7860")
print()
