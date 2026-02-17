# Environment Configuration Files

This directory contains comprehensive Azure scenario templates for the ingest-o-bot document processing pipeline.

## 📁 Available Scenarios

### Scenario 1: Full Azure Stack with Local Input
- **File**: `.env.scenario-01-azure-full-local.example`
- **Use Case**: Enterprise processing with maximum quality
- **Stack**: Azure DI + Azure OpenAI + Azure Search + Local files
- **Cost**: $3-5 per 1000 pages

### Scenario 2: Full Azure Stack with Blob Storage
- **File**: `.env.scenario-02-azure-full-blob.example`
- **Use Case**: Production cloud-native deployment
- **Stack**: Azure DI + Azure OpenAI + Azure Search + Blob Storage
- **Cost**: $3-5 per 1000 pages + storage

### Scenario 3: Azure + ChromaDB (Cost Optimized)
- **File**: `.env.scenario-03-azure-di-chromadb.example`
- **Use Case**: High-quality extraction with cost savings
- **Stack**: Azure DI + Azure OpenAI + ChromaDB (local)
- **Cost**: $2-3 per 1000 pages (saves $250-500/month)

### Scenario 4: Integrated Vectorization (Fastest)
- **File**: `.env.scenario-04-azure-integrated-vectorization.example`
- **Use Case**: Maximum performance with server-side embeddings
- **Cost**: $$$ (~$1000/month) but 2-3x faster

### Scenario 5: Vision-Heavy Processing
- **File**: `.env.scenario-05-azure-vision-heavy.example`
- **Use Case**: Documents with many images, charts, diagrams
- **Cost**: $0.15-0.60 per image (can be expensive!)

### Scenario 6: Multilingual Processing
- **File**: `.env.scenario-06-azure-multilingual.example`
- **Use Case**: 100+ language support
- **Cost**: $330-950/month (Cohere) OR $280-1060/month (HuggingFace)

## 🚀 Quick Start

1. Choose a scenario based on your needs
2. Copy to .env: `cp envs/.env.scenario-01-azure-full-local.example .env`
3. Update credentials with your actual Azure values
4. Test: `python -m ingestor.cli --pdf test.pdf`

## 📊 Cost Comparison

| Scenario | Monthly Fixed | Per 1000 Pages |
|----------|---------------|----------------|
| 1 & 2: Full Azure | $250-500 | $3-5 |
| 3: ChromaDB | $0 | $2-3 |
| 4: Integrated Vec | $1000+ | $3-5 |
| 5: Vision Heavy | $250-500 | $5-20+ |
| 6: Multilingual | $330-950 | $3-5 |
