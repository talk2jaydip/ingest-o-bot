# Scripts

Utility scripts for running and testing ingestor.

## Available Scripts

### UI Launcher
- **launch_ui.bat** (Windows) / **launch_ui.sh** (Linux/Mac)
  - Launches the Gradio web interface
  - Usage: `./scripts/launch_ui.sh` or `scripts\launch_ui.bat`
  - Opens UI at http://localhost:7860

### Testing
- **test_index_ops.bat** (Windows) / **test_index_ops.sh** (Linux/Mac)
  - Tests index operations (create, delete, update)
  - Usage: `./scripts/test_index_ops.sh` or `scripts\test_index_ops.bat`

### Pipeline Testing
- **run_test.bat** (Windows) / **run_test.sh** (Linux/Mac)
  - Runs full pipeline tests
  - Usage: `./scripts/run_test.sh` or `scripts\run_test.bat`

## Running Scripts

### Windows
```cmd
cd c:\Work\ingestor
scripts\launch_ui.bat
```

### Linux/Mac
```bash
cd /path/to/ingestor
chmod +x scripts/*.sh
./scripts/launch_ui.sh
```

## After Installation

If you installed the package with `pip install -e .`, you can use the CLI commands:
```bash
ingestor --help          # CLI interface
ingestor-ui              # Launch UI
```
