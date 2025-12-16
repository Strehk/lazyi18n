# lazyi18n 📚🎯

A terminal UI for managing i18next translation files, inspired by lazygit. Wrangle your nested JSON translation files with ease, identify missing translations at a glance, and maintain consistency across locales.

## Why lazyi18n?

Editing i18n files manually is painful:
- **Missing translations** are hard to spot
- **Nested JSON** is awkward to navigate
- **No workflow** for bulk updates
- **Manual comparison** between locales is tedious

lazyi18n brings the UX of lazygit to translation management.

## Features (Planned & Implemented)

### Phase 1: Core ✅ COMPLETE
- [x] File loader for discovering JSON files
- [x] Flatten/unflatten utilities for dot-notation
- [x] Gap analyzer for finding missing translations
- [x] Safe JSON writer with atomic operations
- [x] Central TranslationProject orchestrator

### Phase 2: UI ✅ ENHANCED!
- [x] Textual app scaffold with three-pane layout
- [x] Tree widget for keys with gap highlighting (⚠️ missing, ✓ complete)
- [x] Values pane showing translations per locale
- [x] Status bar with coverage metrics
- [x] **NEW!** Single-key shortcuts (q, s, r, ?, e)
- [x] **NEW!** Inline editing mode with modal dialog
- [x] **NEW!** Tab navigation in edit mode
- [x] **NEW!** 43 comprehensive unit tests
- [x] **NEW!** Search/filter by key name (/)
- [x] **NEW!** Key creation wizard (n)
- [x] **NEW!** Bulk fill missing translations (b)

### Phase 3: Integration 📋 PLANNED
- [ ] CLI packaging with argparse
- [ ] LazyVim/Neovim integration (toggleterm wrapper)
- [ ] lazy.nvim plugin spec
- [ ] Configuration file support

## Architecture

```
lazyi18n/
├── core/
│   ├── loader.py       # File discovery & loading
│   ├── flatten.py      # JSON ↔ dot-notation utils
│   ├── analyzer.py     # Gap detection & coverage
│   ├── writer.py       # Safe JSON persistence
│   ├── project.py      # Central orchestrator
│   └── __init__.py
├── ui/
│   ├── app.py          # Textual components
│   └── __init__.py
├── main.py             # Entry point
├── test_core.py        # Core validation
├── examples/           # Sample translation files
│   ├── en.json
│   └── de.json
└── requirements.txt
```

## Installation

```bash
git clone <repo>
cd lazyi18n
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Quick Start

### 1. Run the validation
```bash
python3 quickstart.py
```

### 2. Test the core engine
```bash
python3 test_core.py
```

### 3. Launch the TUI
```bash
# Using the launcher script (recommended)
./lazyi18n.sh examples/

# Or activate venv manually
source .venv/bin/activate.fish  # or .venv/bin/activate for bash/zsh
python main.py examples/

# Or with your own i18n files
./lazyi18n.sh /path/to/your/locales/
```

### 4. Navigate and explore
- **Arrow keys**: Navigate the tree
- **Enter** or **e**: Edit selected translation (opens modal)
- **/**: Search/filter keys
- **n**: Create a new key
- **b**: Bulk fill missing translations
- **s**: Save changes
- **r**: Reload from disk
- **q**: Quit
- **?**: Show help
- **Tab**: Next field (in edit mode)
- **Escape**: Cancel edit

### 5. Try inline editing!
1. Navigate to any key with ↑/↓
2. Press **Enter** to edit
3. Modal dialog appears with input fields for all locales
4. Use **Tab** to navigate between fields
5. Press **Ctrl+S** to save or **Esc** to cancel
6. Changes are tracked, use **s** in main view to save to disk

## Usage (Current Workflow)

1. **Launch**: `./lazyi18n.sh /path/to/translations` or `lazyi18n /path/to/locales`
2. **Browse**: Navigate tree to find keys with gaps (marked with ⚠️) or complete (✓)
3. **Edit**: Select a key, press **Enter** to open edit modal
4. **Translate**: Fill in values for each locale, use **Tab** to navigate
5. **Save**: Press **Ctrl+S** in edit mode, then **s** in main view to write to disk
6. **Verify**: Coverage bar updates in real-time, tree markers refresh on save

## Dependencies

```
textual>=6.10.0     # TUI framework (by Will McGugan, creator of Rich)
rich>=14.2.0        # Beautiful terminal rendering
```

## LazyVim Integration (Phase 3)

### Quick Setup

1. **Copy lazyi18n to a standard location:**
```bash
mkdir -p ~/.local/share
cp -r /Users/tadestrehk/Developer/lazyi18n ~/.local/share/lazyi18n
```

2. **Add the plugin to LazyVim:**
```bash
cp nvim-plugin-lazyi18n.lua ~/.config/nvim/lua/plugins/lazyi18n.lua
```

3. **Restart Neovim and use:**
```vim
" Press leader + t + i
<leader>ti

" Or run command
:Lazyi18n
```

The TUI will open in a floating terminal via toggleterm.nvim!

See [LAZYVIM_SETUP.md](LAZYVIM_SETUP.md) for detailed installation instructions.

## Design Decisions

### Why Python + Textual?
- **Textual**: CSS-like layout, reactive data binding, gorgeous by default
- **Python**: Superior dict/JSON handling, rich ecosystem, great for CLI tools
- **Alternative considered**: TypeScript (Ink/Blessed) - good but less mature

### Flat Structure
- Flattened dot-notation (e.g., `auth.login.btn`) makes comparison trivial
- Easy to display in trees and tables
- Unflatten only on save to preserve nested structure

### Atomic Writes
- Prevents data corruption if write is interrupted
- Temporary file written first, then atomically moved
- Backups created before overwrite

## Roadmap

### Completed ✅
- [x] Core engine with file loading, gap analysis, safe writing
- [x] Beautiful TUI with tree, values, and status panes
- [x] Inline editing with modal dialog
- [x] Single-key keyboard shortcuts
- [x] 43 comprehensive unit tests
- [x] LazyVim integration config

### Next Up 🔨
- [ ] Search/filter by key name (press /)
- [ ] Bulk operations (fill all missing translations)
- [ ] Key creation wizard (press n)
- [ ] Pluralization rules support (i18next format)
- [ ] Context/namespace support
- [ ] Export/import for external translators (CSV)
- [ ] Git diff integration
- [ ] AI suggestions for missing translations
- [ ] Watch mode (auto-reload on file change)

## Contributing

Contributions welcome! Areas needing help:
- [ ] Search/filter implementation (press / to activate)
- [ ] Bulk edit operations for missing keys
- [ ] Neovim plugin improvements
- [ ] Additional test cases
- [ ] UI polish (themes, custom colors)
- [ ] Documentation & tutorials

## Testing

Run the comprehensive test suite:

```bash
# Run all 43 unit tests
python3 -m unittest discover tests -v

# Test specific module
python3 -m unittest tests.test_flatten -v

# With coverage (if installed)
python3 -m coverage run -m unittest discover tests
python3 -m coverage report
```

## License

MIT

## Acknowledgments

- **Will McGugan** for Textual & Rich
- **lazygit** for the UX inspiration
- Your sanity, for finally getting a break from JSON wrangling

---

**Built with ❤️ for tired translators**
