# UI Element Dumpers

This repository contains comprehensive tools for dumping UI elements from macOS applications in beautiful tree format.

## Files Overview

### 1. `ui_dumper_main.py` ⭐ **RECOMMENDED**
- The most polished and user-friendly dumper
- Beautiful emoji-based tree output
- Works with atomacos library
- Categorizes UI elements by type
- Handles multiple applications
- **No limiting - dumps everything**

### 2. `ui_dumper_advanced.py`
- Full-featured dumper using ApplicationServices and CoreGraphics
- Requires accessibility permissions
- Supports all applications
- Advanced tree formatting
- Handles Chrome specifically with multiple approaches

### 3. `ui_dumper_basic.py`
- Basic dumper using ApplicationServices
- Requires accessibility permissions
- Simple tree output
- Good for learning the basics

### 4. `ui_dumper_atomac.py`
- Uses atomac library for UI automation
- Finds toolbar buttons specifically
- Good for button-focused analysis

### 5. `ui_dumper_share.py`
- Specialized for finding and clicking share buttons
- Uses atomac library
- Includes menu navigation

## Usage

### Main Dumper (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# System overview
python ui_dumper_main.py --system

# All applications
python ui_dumper_main.py --all

# Specific applications
python ui_dumper_main.py --chrome
python ui_dumper_main.py --safari
python ui_dumper_main.py --cursor
python ui_dumper_main.py "Application Name"
```

### Other Dumpers

```bash
# Advanced dumper (Chrome-focused)
python ui_dumper_advanced.py --chrome

# Basic dumper
python ui_dumper_basic.py

# Atomac-based dumper
python ui_dumper_atomac.py

# Share button finder
python ui_dumper_share.py
```

## Features

### System Overview (`--system`)
- Shows total processes and unique applications
- Top applications by process count
- Display information
- Categorized application listing

### Application Dumping
- **Windows**: Shows all windows with titles and dimensions
- **Toolbars**: Finds and lists all toolbars
- **Buttons**: Discovers all buttons with titles and descriptions
- **Tab Groups**: Shows tab organization
- **Text Fields**: Lists input fields
- **Static Text**: Shows text elements
- **Groups**: Displays UI groups
- **Lists**: Finds list elements
- **Tables**: Shows table structures
- **Images**: Lists image elements
- **Checkboxes**: Finds checkboxes
- **Radio Buttons**: Shows radio button groups
- **Sliders**: Lists slider controls
- **Combo Boxes**: Finds dropdown menus
- **Pop-up Buttons**: Shows popup controls
- **Menus**: Lists menu structures
- **Scroll Areas**: Finds scrollable regions
- **Browsers**: Discovers browser elements

### Beautiful Output
- 🌳 Tree structure with emojis
- 🪟 Windows
- 🔘 Buttons
- 🔧 Toolbars
- 📑 Tab Groups
- 📝 Text Fields
- 📄 Static Text
- 📦 Groups
- 📋 Lists
- 📊 Tables
- 🖼️ Images
- ☑️ Checkboxes
- 🎚️ Sliders
- 🌐 Browsers
- 🚀 Applications

## Requirements

- macOS (uses ApplicationServices and CoreGraphics)
- Python 3.13+
- Virtual environment with required packages:
  - `atomacos` (for UI automation)
  - `pyobjc` (for macOS integration)

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install atomacos
```

## Examples

### Chrome Analysis

```bash
python ui_dumper_main.py --chrome
```

Output shows:
- 2 Chrome windows found
- Window 1: "Find in page" dialog
- Window 2: Main browser window with full UI tree
- 23 buttons (Close, New Tab, Back, Forward, etc.)
- 3 toolbars (Bookmarks, Saved Tab Groups)
- 1 tab group with multiple tabs
- 2 text fields (Address bar, Find field)
- 19 radio buttons (representing tabs)
- 12 pop-up buttons (Extensions, Chrome menu, etc.)

### System Overview

```bash
python ui_dumper_main.py --system
```

Shows:
- 457 total processes
- 367 unique applications
- Top applications by process count
- Categorized application listing

## Technical Details

The dumpers use multiple approaches:

1. **ApplicationServices**: Direct accessibility API access
2. **CoreGraphics**: Window listing and geometry
3. **atomacos**: High-level UI automation
4. **System Commands**: Process listing and system info

The tools handle:
- Permission requirements
- Error handling
- Circular reference detection
- Depth limiting
- Beautiful formatting
- **No output limiting - shows everything**

## Troubleshooting

### Accessibility Permissions
If you get permission errors, grant accessibility permissions:
1. System Preferences → Security & Privacy → Privacy
2. Select "Accessibility" from the left sidebar
3. Add your terminal/IDE to the list

### Missing Dependencies
```bash
pip install atomacos pyobjc-framework-ApplicationServices
```

### No Windows Found
- Ensure the application is running
- Try clicking on the application window
- Some applications may not expose their UI through accessibility APIs

### Cursor/VS Code Limited Output
This is normal! Electron-based applications (Cursor, VS Code, Discord) have limited accessibility support. The dumper shows everything that's available through accessibility APIs.