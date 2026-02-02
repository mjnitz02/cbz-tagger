# Reflex GUI Migration

This document describes the Reflex GUI implementation for CBZ Tagger, which provides a modern alternative to the NiceGUI interface.

## Overview

The Reflex GUI is a complete reimplementation of the CBZ Tagger web interface using the Reflex framework (https://reflex.dev). It provides the same functionality as the NiceGUI version while leveraging Reflex's modern architecture.

## Architecture

### Directory Structure

```
cbz_tagger/reflex_gui/
├── __init__.py
├── reflex_app.py           # Main application entry point
├── states/                  # State management
│   ├── __init__.py
│   ├── base_state.py       # Base state with locking & shared scanner
│   ├── series_state.py     # Series page state
│   ├── manage_state.py     # Manage page state
│   ├── config_state.py     # Config page state
│   └── log_state.py        # Logs page state
├── pages/                   # Page definitions
│   ├── __init__.py
│   ├── series.py           # Series table page (/)
│   ├── manage.py           # Manage series page (/manage)
│   ├── config.py           # Configuration page (/config)
│   └── logs.py             # Logs page (/logs)
├── components/              # Reusable UI components
│   ├── __init__.py
│   ├── navbar.py           # Navigation bar
│   └── series_table.py     # Series data table
├── utils/                   # Utilities
│   ├── __init__.py
│   └── log_handler.py      # File-based log handler
└── lifespan/               # Background tasks (reserved for future use)
    └── __init__.py
```

### Key Components

#### BaseState (states/base_state.py)
- Provides shared scanner instance across all sessions
- Implements database locking mechanism to prevent concurrent operations
- Provides `run_sync_operation()` method to bridge async/sync operations
- Includes notification system for user feedback

#### State Management
- **SeriesState**: Manages series table data, refresh operations, column visibility
- **ManageState**: Handles adding/deleting series, searching, chapter management
- **ConfigState**: Displays server configuration
- **LogState**: Manages log file reading and display

#### Background Timer
Implemented in `reflex_app.py` as a lifespan task:
- Runs periodic scanner refresh every TIMER_DELAY seconds
- Skips first run (first_scan logic)
- Respects database locking to avoid conflicts

#### Logging
File-based logging system:
- Logs written to `/tmp/cbz_tagger_gui.log`
- Max 1000 lines displayed in GUI
- Custom FileLogHandler in `utils/log_handler.py`

## Running the Reflex GUI

### Development Mode

```bash
make dev
```

This starts the Reflex development server with:
- GUI_MODE=true
- USE_REFLEX=true
- Hot reload enabled
- Access at http://localhost:8080

### Production Mode (Docker)

1. Build the Docker image:
```bash
docker build -t cbz-tagger .
```

2. Run with Reflex GUI:
```bash
docker run -e GUI_MODE=true -e USE_REFLEX=true \
  -v $(pwd)/config:/config \
  -v $(pwd)/scan:/scan \
  -v $(pwd)/storage:/storage \
  -p 8080:8080 \
  cbz-tagger
```

Or use docker-compose with:
```yaml
environment:
  - GUI_MODE=true
  - USE_REFLEX=true
```

## Environment Variables

- `GUI_MODE=true`: Enable GUI mode
- `USE_REFLEX=true`: Use Reflex GUI instead of NiceGUI
- `TIMER_DELAY`: Scanner refresh interval in seconds (default: 600)
- `CONFIG_PATH`: Configuration directory path
- `SCAN_PATH`: Scan directory path
- `STORAGE_PATH`: Storage directory path
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Feature Parity with NiceGUI

The Reflex GUI provides exact feature parity with the NiceGUI implementation:

### Series Page
- ✅ Series table with sortable columns
- ✅ Column visibility toggles (Entity ID, Metadata Updated, Plugin)
- ✅ Refresh Table button
- ✅ Refresh Database button (full scan)
- ✅ Status emojis (completed, ongoing, hiatus, cancelled)
- ✅ Date color coding (< 45d green, 45-90d orange, > 90d red)
- ✅ Legend display

### Manage Page
- ✅ Search for new series via MDX API
- ✅ Series dropdown with filtering
- ✅ Name selector for alternative titles
- ✅ Backend selector (MDX, WBC, KAL)
- ✅ Backend ID input for non-MDX sources
- ✅ Mark all chapters as tracked option
- ✅ Add new series functionality
- ✅ Series list management
- ✅ Delete series
- ✅ Reset chapter tracking
- ✅ Clean orphaned files

### Config Page
- ✅ Display all server configuration
- ✅ Read-only table view

### Logs Page
- ✅ Log file viewer (1000 line buffer)
- ✅ Refresh logs button
- ✅ Clear logs button
- ✅ Monospace font display
- ✅ Auto-refresh toggle (UI only, polling done manually)

## Database Operations

All database operations use the same locking mechanism as NiceGUI:
- Class-level `_scanning_state` boolean prevents concurrent operations
- Operations run in asyncio executor to avoid blocking the UI
- Scanner instance shared across all sessions via BaseState

## Known Differences from NiceGUI

1. **Logging**: Uses file-based logging instead of direct UI push
   - Logs written to `/tmp/cbz_tagger_gui.log`
   - Polling-based refresh instead of real-time push
   - This is simpler and more reliable than the NiceGUI approach

2. **Component Library**: Uses Reflex components instead of NiceGUI/Quasar
   - Similar visual appearance maintained
   - Some minor styling differences due to component library

3. **Startup**: Reflex requires separate frontend build step
   - Development: `reflex run` handles both frontend and backend
   - Production: Use `reflex run --env prod`

## Migration Notes

The old NiceGUI code is preserved in `cbz_tagger/gui/` and can be removed once the Reflex GUI is fully validated. To switch back to NiceGUI, set `USE_REFLEX=false` or omit the variable.

## Dependencies

Added to `pyproject.toml`:
- `reflex>=0.6.0`

Docker image includes:
- Node.js and npm (required for Reflex frontend compilation)

## Configuration Files

- `rxconfig.py`: Reflex configuration (app name, ports, plugins)
- `Makefile`: Added `make dev` command for local development

## Future Enhancements

Possible improvements for the future:
1. WebSocket-based real-time log updates
2. Enhanced UI styling with custom themes
3. Additional visualizations (charts, graphs)
4. Mobile-responsive improvements
5. Dark mode support
