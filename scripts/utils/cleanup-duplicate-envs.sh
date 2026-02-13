#!/bin/bash
# Script to remove duplicate and old env files
# Run this to clean up unnecessary env files

echo "============================================"
echo "Cleaning up duplicate/old env files"
echo "============================================"
echo ""

echo "Removing old/duplicate files..."

# Remove root duplicate
[ -f .env.example ] && rm .env.example && echo "Removed: .env.example"

# Remove old envs/ files
cd envs

[ -f .env.chromadb.example ] && rm .env.chromadb.example && echo "Removed: envs/.env.chromadb.example"
[ -f .env.cohere.example ] && rm .env.cohere.example && echo "Removed: envs/.env.cohere.example"
[ -f .env.example ] && rm .env.example && echo "Removed: envs/.env.example"
[ -f .env.example.dev ] && rm .env.example.dev && echo "Removed: envs/.env.example.dev"
[ -f .env.example.prod ] && rm .env.example.prod && echo "Removed: envs/.env.example.prod"
[ -f .env.example.staging ] && rm .env.example.staging && echo "Removed: envs/.env.example.staging"
[ -f .env.hybrid.example ] && rm .env.hybrid.example && echo "Removed: envs/.env.hybrid.example"
[ -f .env.scenario-azure-cohere.example ] && rm .env.scenario-azure-cohere.example && echo "Removed: envs/.env.scenario-azure-cohere.example"
[ -f .env.scenario-azure-openai-default.example ] && rm .env.scenario-azure-openai-default.example && echo "Removed: envs/.env.scenario-azure-openai-default.example"
[ -f .env.scenario-cost-optimized.example ] && rm .env.scenario-cost-optimized.example && echo "Removed: envs/.env.scenario-cost-optimized.example"
[ -f .env.scenario-development.example ] && rm .env.scenario-development.example && echo "Removed: envs/.env.scenario-development.example"
[ -f .env.scenario-multilingual.example ] && rm .env.scenario-multilingual.example && echo "Removed: envs/.env.scenario-multilingual.example"
[ -f .env.scenarios.example ] && rm .env.scenarios.example && echo "Removed: envs/.env.scenarios.example"

cd ..

echo ""
echo "============================================"
echo "Cleanup complete!"
echo "============================================"
echo ""
echo "KEPT files (6 total):"
echo "  envs/.env.azure-local-input.example"
echo "  envs/.env.azure-chromadb-hybrid.example"
echo "  envs/.env.offline-with-vision.example"
echo "  envs/.env.hybrid-scenarios.example"
echo "  examples/playbooks/.env.basic-pdf.example"
echo "  examples/playbooks/.env.production.example"
echo ""
echo "Now run: git add -A"
echo "Then: git commit -m 'chore: Remove duplicate env files'"
echo ""
