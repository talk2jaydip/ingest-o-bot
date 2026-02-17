"""Export current index schema and compare with original."""
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ingestor.index import IndexDeploymentManager
from ingestor.config import SearchConfig, AzureOpenAIConfig
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Load configs
search_config = SearchConfig.from_env()
openai_config = AzureOpenAIConfig.from_env()

# Create manager
manager = IndexDeploymentManager(
    endpoint=search_config.endpoint,
    api_key=search_config.api_key,
    index_name=search_config.index_name,
    openai_endpoint=openai_config.endpoint,
    openai_deployment=openai_config.emb_deployment,
    openai_key=openai_config.api_key
)

# Export current schema
print(f"Exporting current index schema: {search_config.index_name}")
current_schema_file = manager.export_schema_to_json("current_index_schema.json")
print(f"✓ Exported to: {current_schema_file}")

# Load both schemas
with open("current_index_schema.json", "r") as f:
    current = json.load(f)

with open("oringal_index.json", "r") as f:
    original = json.load(f)

print("\n" + "="*70)
print("COMPARISON RESULTS")
print("="*70)

# Compare index names
print(f"\nIndex Names:")
print(f"  Original: {original.get('name')}")
print(f"  Current:  {current.get('name')}")

# Compare field counts
orig_fields = {f['name']: f for f in original.get('fields', [])}
curr_fields = {f['name']: f for f in current.get('fields', [])}

print(f"\nField Counts:")
print(f"  Original: {len(orig_fields)} fields")
print(f"  Current:  {len(curr_fields)} fields")

# Find differences in fields
missing_fields = set(orig_fields.keys()) - set(curr_fields.keys())
new_fields = set(curr_fields.keys()) - set(orig_fields.keys())
common_fields = set(orig_fields.keys()) & set(curr_fields.keys())

if missing_fields:
    print(f"\n⚠️  Fields in ORIGINAL but NOT in CURRENT:")
    for field_name in sorted(missing_fields):
        print(f"     - {field_name}")

if new_fields:
    print(f"\n✓ New fields in CURRENT:")
    for field_name in sorted(new_fields):
        print(f"     + {field_name}")

# Compare scoring profiles
orig_profiles = {p['name']: p for p in original.get('scoringProfiles', [])}
curr_profiles = {p['name']: p for p in current.get('scoringProfiles', [])}

print(f"\nScoring Profiles:")
print(f"  Original: {len(orig_profiles)} profiles - {list(orig_profiles.keys())}")
print(f"  Current:  {len(curr_profiles)} profiles - {list(curr_profiles.keys())}")

# Compare suggesters
orig_suggesters = original.get('suggesters', [])
curr_suggesters = current.get('suggesters', [])

print(f"\nSuggesters:")
if orig_suggesters:
    print(f"  Original: {orig_suggesters[0].get('name')} with fields {orig_suggesters[0].get('sourceFields')}")
else:
    print(f"  Original: None")

if curr_suggesters:
    print(f"  Current:  {curr_suggesters[0].get('name')} with fields {curr_suggesters[0].get('sourceFields')}")
else:
    print(f"  Current:  None")

# Compare semantic configuration
orig_semantic = original.get('semantic', {}).get('configurations', [])
curr_semantic = current.get('semantic', {}).get('configurations', [])

print(f"\nSemantic Configuration:")
if orig_semantic:
    print(f"  Original: {orig_semantic[0].get('name')}")
else:
    print(f"  Original: None")

if curr_semantic:
    print(f"  Current:  {curr_semantic[0].get('name')}")
else:
    print(f"  Current:  None")

# Vector search comparison
orig_vector = original.get('vectorSearch', {})
curr_vector = current.get('vectorSearch', {})

print(f"\nVector Search:")
print(f"  Original algorithms: {len(orig_vector.get('algorithms', []))}")
print(f"  Current algorithms:  {len(curr_vector.get('algorithms', []))}")
print(f"  Original profiles: {len(orig_vector.get('profiles', []))}")
print(f"  Current profiles:  {len(curr_vector.get('profiles', []))}")

print("\n" + "="*70)
print("DETAILED FIELD COMPARISON (Common Fields)")
print("="*70)

# Compare common fields in detail
field_differences = []
for field_name in sorted(common_fields):
    orig_field = orig_fields[field_name]
    curr_field = curr_fields[field_name]

    differences = []
    for key in set(list(orig_field.keys()) + list(curr_field.keys())):
        if key in ['synonymMaps', 'stored']:  # Skip these
            continue
        orig_val = orig_field.get(key)
        curr_val = curr_field.get(key)
        if orig_val != curr_val:
            differences.append(f"{key}: {orig_val} → {curr_val}")

    if differences:
        field_differences.append((field_name, differences))

if field_differences:
    print(f"\n⚠️  Fields with differences:")
    for field_name, diffs in field_differences:
        print(f"\n  {field_name}:")
        for diff in diffs:
            print(f"    {diff}")
else:
    print("\n✓ All common fields match!")

print("\n" + "="*70)
