# lazyI18n 📚🎯

A terminal UI for managing i18next translation files, inspired by lazygit. Wrangle your nested JSON translation files with ease, identify missing translations at a glance, and maintain consistency across locales.

## Why lazyi18n?

Editing i18n files manually is painful:
- **No useful integration in your editor workflow**
- **Missing translations** are hard to spot
- **Nested JSON** is awkward to navigate
- **Manual comparison** between locales is tedious

lazyi18n brings the UX of lazygit to translation management. It's a TUI that helps you:
- **Visualize translation keys** in a tree structure
- **Highlight gaps** in translations across locales
- **Integrate with LazyVim/Neovim** for seamless workflow

## Planned Features
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
git clone https://github.com/Strehk/lazyi18n
cd lazyi18n

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate.fish  # or .venv/bin/activate for bash/zsh

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
- **Space**: Edit selected translation (opens modal) or toggle branch
- **d**: Delete selected key (with confirmation)
- **/**: Search/filter keys
- **e**: Toggle edited keys filter
- **m**: Toggle missing translations filter
- **n**: Create a new key
- **b**: Bulk fill missing translations
- **s**: Save changes
- **r**: Reload from disk
- **q**: Quit
- **?**: Show help
- **Tab**: Next field (in edit mode)
- **Escape**: Cancel edit

## Usage (Current Workflow)

1. **Launch**: `./lazyi18n.sh /path/to/translations` or `lazyi18n /path/to/locales`
2. **Browse**: Navigate tree to find keys with gaps (marked with ⚠️) or complete (✓)
3. **Edit**: Select a key, press **Space** to open edit modal
4. **Translate**: Fill in values for each locale, use **Tab** to navigate
5. **Save**: Press **Ctrl+S** in edit mode, then **s** in main view to write to disk
6. **Verify**: Coverage bar updates in real-time, tree markers refresh on save

## Dependencies

```
textual>=6.10.0     # TUI framework (by Will McGugan, creator of Rich)
rich>=14.2.0        # Beautiful terminal rendering
```

## LazyVim Integration

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
- [ ] Bulk operations (fill all missing translations)
- [ ] Pluralization rules support (i18next format)
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

MIT. See [LICENSE](LICENSE) for details.

---

**Built with ❤️ in Germany**
