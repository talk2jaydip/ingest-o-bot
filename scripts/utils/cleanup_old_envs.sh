#!/bin/bash
# Cleanup script to remove old .env files
# Keeps only: .env (production) and the 6 new scenario files

echo "Cleaning up old environment files..."
echo ""

# Delete old envs/*.example files
cd envs
rm -f .env.azure-chromadb-hybrid.example
rm -f .env.azure-local-input
rm -f .env.chromadb.example
rm -f .env.cohere.example
rm -f .env.example
rm -f .env.example.dev
rm -f .env.example.prod
rm -f .env.example.staging
rm -f .env.hybrid.example
rm -f .env.hybrid-scenarios.example
rm -f .env.offline-with-vision.example
rm -f .env.scenario-azure-cohere.example
rm -f .env.scenario-azure-openai-default.example
rm -f .env.scenario-cost-optimized.example
rm -f .env.scenario-development.example
rm -f .env.scenario-multilingual.example
rm -f .env.scenarios.example
rm -f env.office-scenario1-azure-di-only.example
rm -f env.office-scenario2-markitdown-only.example
rm -f env.office-scenario3-hybrid-fallback.example
rm -f env.scenario1-local-dev.example
rm -f env.scenario2-blob-prod.example
rm -f env.scenario3-local-to-blob.example
rm -f env.scenario4-blob-to-local.example
rm -f env.scenario5-offline.example
cd ..

# Delete examples/playbooks .env files
cd examples/playbooks
rm -f .env.production.example
rm -f .env.basic-pdf.example
cd ../..

# Delete root backup files
rm -f .env.backup
rm -f .env.example
rm -f .env.azure-chromadb-test
rm -f .env.GLOBAL-ALL-VARIABLES
rm -f .env.local-dev
rm -f test-env-file.env

echo ""
echo "Cleanup complete!"
echo ""
echo "KEPT FILES:"
echo "  - .env (production)"
echo "  - envs/.env.azure-local-input.example (reference)"
echo "  - envs/.env.scenario-01-azure-full-local.example"
echo "  - envs/.env.scenario-02-azure-full-blob.example"
echo "  - envs/.env.scenario-03-azure-di-chromadb.example"
echo "  - envs/.env.scenario-04-azure-integrated-vectorization.example"
echo "  - envs/.env.scenario-05-azure-vision-heavy.example"
echo "  - envs/.env.scenario-06-azure-multilingual.example"
echo ""
