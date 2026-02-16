# Vector Store Browser UI - Enhanced Design

## Overview

The Vector Store Browser provides a unified interface for browsing and inspecting indexed documents from both **Azure AI Search** and **ChromaDB** vector stores.

## Location in UI

**Files Tab → Browse Vector Store (Azure Search / ChromaDB)** accordion (now OPEN by default)

## Visual Structure

```
📁 Files Tab
  └─ 🔍 Browse Vector Store (Azure Search / ChromaDB) ✅ OPEN
      ├─ Header: "🔍 Vector Store Browser"
      ├─ Status Badges: "🔵 Azure Search: Available | 🟢 ChromaDB: Available"
      ├─ Quick Guide (collapsible accordion)
      └─ Vector Store Tabs:
          ├─ 🔵 Azure AI Search Tab
          │   ├─ Connection Status Indicator: "🟢 Connected" or "🔴 Not Connected"
          │   ├─ ⚙️ Configuration Accordion (collapsible)
          │   │   ├─ 🔄 Refresh from Environment button
          │   │   ├─ AZURE_SEARCH_SERVICE textbox
          │   │   ├─ AZURE_SEARCH_INDEX textbox
          │   │   ├─ AZURE_SEARCH_KEY password field
          │   │   ├─ 💾 Save Config (Session) button
          │   │   └─ Status textbox
          │   ├─ Index Name dropdown with 🔄 Refresh
          │   ├─ Index Info textbox
          │   ├─ Search Pattern textbox + 🔍 Search button
          │   ├─ Documents dataframe (Filename, Category, Chunks)
          │   ├─ Statistics textbox
          │   └─ 📄 View Document Details accordion
          │       ├─ Document ID textbox
          │       ├─ View Details button
          │       └─ Tabs: Content | Metadata
          │
          └─ 🟢 ChromaDB Tab
              ├─ Connection Status Indicator: "🟢 Ready (Local)" or "🔴 Not Configured"
              ├─ ⚙️ Configuration Accordion (collapsible)
              │   ├─ 🔄 Refresh from Environment button
              │   ├─ ChromaDB Mode radio: Persistent | In-Memory | Client/Server
              │   ├─ CHROMADB_PERSIST_DIR textbox
              │   ├─ CHROMADB_HOST textbox
              │   ├─ CHROMADB_PORT textbox
              │   ├─ 💾 Save Config (Session) button
              │   └─ Status textbox
              ├─ Collection dropdown with 🔄 Refresh
              ├─ Collection Info textbox
              ├─ Search Pattern textbox + 🔍 Search button
              ├─ Chunks dataframe (Chunk ID, Source, Page, Content Preview)
              ├─ Statistics textbox
              └─ 📄 View Chunk Details accordion
                  ├─ Chunk ID textbox
                  ├─ View Details button
                  └─ Tabs: Content | Metadata
```

## Key Features

### 1. **Modular Tab Design** ✨
- **Separate tabs** for Azure AI Search and ChromaDB
- Easy to add new vector stores (Pinecone, Weaviate, etc.) as new tabs
- Each tab is self-contained with its own configuration

### 2. **Real-Time Connection Status** 🟢🔴
- **Azure Tab**: Shows "🟢 Connected" when service is configured, "🔴 Not Connected" otherwise
- **ChromaDB Tab**: Shows "🟢 Ready (Local/Client/Server)" based on mode, "🔴 Not Configured" if missing
- Status updates dynamically when you save configuration

### 3. **Environment Integration** 🔄
- All configuration values loaded from **active .env file** (selected in Configuration tab)
- "🔄 Refresh from Environment" button to reload from env file
- "💾 Save Config (Session)" button to update runtime environment (session only)

### 4. **Quick Guide** ℹ️
- Collapsible accordion with step-by-step instructions
- Tips for using search patterns, configuration, etc.

### 5. **Search & Browse** 🔍
- **Azure Search**: Search by filename pattern, view document chunks
- **ChromaDB**: Search by source file pattern, view individual chunks
- Pattern support: `*` (all), `filename*`, `*.pdf`, etc.

### 6. **Details Viewer** 📄
- View full content, metadata (JSON), and embeddings
- Separate tabs for Content and Metadata for easy navigation

## How It Works

### Selection Flow
```
User opens Files Tab
  → Vector Store accordion is OPEN by default
  → User sees status badges showing which stores are available
  → User clicks "🔵 Azure AI Search" OR "🟢 ChromaDB" tab
  → Connection status indicator shows if configured
  → User can configure (if needed) or start browsing immediately
```

### Configuration Flow (Azure)
```
1. Click "⚙️ Azure Search Configuration" accordion
2. Click "🔄 Refresh from Environment" to load values from .env
3. Edit AZURE_SEARCH_SERVICE, AZURE_SEARCH_INDEX, AZURE_SEARCH_KEY
4. Click "💾 Save Config (Session)"
5. Connection status updates to "🟢 Connected"
6. Start browsing with Index dropdown + Search pattern
```

### Configuration Flow (ChromaDB)
```
1. Click "⚙️ ChromaDB Configuration" accordion
2. Click "🔄 Refresh from Environment" to load values from .env
3. Select mode: Persistent (Local) | In-Memory | Client/Server
4. Edit CHROMADB_PERSIST_DIR (for Local) or HOST/PORT (for Client/Server)
5. Click "💾 Save Config (Session)"
6. Connection status updates to "🟢 Ready (Local)" or "🟢 Ready (Client/Server)"
7. Start browsing with Collection dropdown + Search pattern
```

## Environment Variables

### Azure AI Search
- `AZURE_SEARCH_SERVICE` - Search service name (required)
- `AZURE_SEARCH_INDEX` - Index name (required)
- `AZURE_SEARCH_KEY` - API key (required)

### ChromaDB
- `CHROMADB_PERSIST_DIR` - Local storage path (default: `./chroma_db`)
- `CHROMADB_HOST` - Remote server hostname (for Client/Server mode)
- `CHROMADB_PORT` - Remote server port (for Client/Server mode)

## Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| 🟢 Connected / Ready | Vector store is properly configured |
| 🔴 Not Connected / Not Configured | Missing required configuration |
| 🟡 In-Memory Mode | ChromaDB running in memory (no persistence) |
| 🔵 Available | Azure AI Search library installed |
| 🟢 Available | ChromaDB library installed |
| ⚠️ | Warning or unavailable |

## Benefits of Enhanced Design

1. **Clear Selection** - Tabs make it obvious which vector store you're using
2. **Status Visibility** - No guessing if configuration is working
3. **Modularity** - Easy to add more vector stores (Pinecone, Weaviate, etc.)
4. **Self-Documenting** - Quick Guide and status badges explain everything
5. **Immediate Feedback** - Connection status updates in real-time
6. **Environment Sync** - Always in sync with your active .env file

## Testing Checklist

- [ ] Open Files tab - accordion should be OPEN by default
- [ ] See status badges showing available vector stores
- [ ] Click Azure AI Search tab - see connection status
- [ ] Click ChromaDB tab - see connection status
- [ ] Configure Azure Search - status updates to "🟢 Connected"
- [ ] Configure ChromaDB - status updates to "🟢 Ready"
- [ ] Search documents in Azure Search
- [ ] Search chunks in ChromaDB
- [ ] View document/chunk details with Content and Metadata tabs
- [ ] Refresh from environment - values reload correctly

## Troubleshooting

**Q: I don't see any tabs**
- Make sure at least one vector store library is installed:
  - `pip install azure-search-documents` (for Azure Search)
  - `pip install chromadb` (for ChromaDB)

**Q: Connection status shows "🔴 Not Connected"**
- Click "🔄 Refresh from Environment" to load from .env file
- Or manually enter configuration and click "💾 Save Config (Session)"
- Check your .env file has required variables

**Q: ChromaDB shows "🔴 Not Configured"**
- Set `CHROMADB_PERSIST_DIR=./chroma_db` in your .env file
- Or configure manually in the UI

**Q: Search returns no results**
- Use `*` pattern to list all items
- Check your index/collection has data
- Verify connection status is "🟢"
