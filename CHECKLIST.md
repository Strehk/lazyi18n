# lazyi18n Implementation Checklist & Battle Plan

> Your roadmap to sanity in i18n management. Check these off as you conquer translation wrangling.

## 📋 Phase 1: The Core Engine ✅ DONE

The foundational Python classes that make everything work.

- [x] **1.1 File Loader** (`core/loader.py`)
  - Discovers JSON files in directory (flat or nested structure)
  - Loads multiple locales simultaneously
  - Handles missing files gracefully
  - ✅ Implemented: `TranslationFileLoader`, `LocaleFile`

- [x] **1.2 Flatten/Unflatten** (`core/flatten.py`)
  - Converts `{"auth": {"login": "Hi"}}` → `{"auth.login": "Hi"}`
  - Reverses for saving without destroying nesting
  - Helper functions for dot-notation access
  - ✅ Implemented: `flatten_json()`, `unflatten_json()`, `get_nested_value()`, `set_nested_value()`

- [x] **1.3 Gap Analysis** (`core/analyzer.py`)
  - Compares keys across locales
  - Identifies missing translations
  - Calculates coverage percentage
  - Returns structured gap report
  - ✅ Implemented: `TranslationGapAnalyzer`, `TranslationGap`

- [x] **1.4 Safe Writer** (`core/writer.py`)
  - Writes JSON with proper formatting
  - Creates backups before overwrite
  - Atomic writes (temp file → move)
  - ✅ Implemented: `TranslationWriter` with `write()` and `write_atomic()`

- [x] **1.5 Project Model** (`core/project.py`)
  - Central orchestrator for all operations
  - Manages state (loaded files, changes)
  - Tracks unsaved changes per locale
  - ✅ Implemented: `TranslationProject`, `ProjectChange`

**Test it**: `python3 test_core.py`

---

## 🎨 Phase 2: The User Interface ✅ DONE

Building the beautiful TUI that users interact with.

### 2.1 Textual App Scaffold ✅
- [x] Create `App` subclass with Textual framework
- [x] CSS grid layout (3-column, 3-row)
- [x] Header (title bar)
- [x] Footer (key bindings help)
- [x] Three-pane layout structure
- ✅ Implemented in `main.py`

**Status**: Basic structure ready, needs component integration

### 2.2 Tree Widget ✅ DONE
- [x] Tree widget showing all keys
- [x] Group by first-level namespace (e.g., "auth", "dashboard")
- [x] Mark gaps with ⚠️ emoji
- [x] Click to select key
- [x] Search/filter keys
- [x] Expand/collapse with arrow keys

### 2.3 Values Pane ✅ DONE
- [x] Show selected key's translations
- [x] Display all locale values side-by-side
- [x] Color code missing (red) vs present (green)
- [x] Inline editing mode (press 'e' to edit)
- [x] Tab between locale inputs (in modal)

### 2.4 Keyboard Bindings ✅ DONE
- [x] s → Save changes
- [x] q → Quit
- [x] r → Reload from disk
- [x] ? → Show help
- [x] e → Edit selected value
- [x] Tab → Next locale input (in modal)
- [x] Escape → Cancel edit
- [x] n → New key
- [x] d → Delete key (with Enter/Escape confirmation)
- [x] / → Search/filter mode

### 2.5 Dashboard ✅ DONE
- [x] Show coverage per locale
- [x] Display unsaved changes
- [x] Show last action (Save, Reload, etc)
- [x] Update in real-time
- [x] Visual indicators (Green/Red)
- ✅ Implemented in `StatusDisplay`

---

## 🚀 Phase 3: Integration & Packaging 📋 PLANNED

Making it accessible from LazyVim and the command line.

### 3.1 CLI Packaging
- [ ] `setup.py` or `pyproject.toml`
- [ ] Entry point: `lazyi18n` command
- [ ] Support multiple directory arguments
- [ ] `--help` documentation
- [ ] Version info

**Implementation**:
```bash
lazyi18n /path/to/locales
lazyi18n --version
lazyi18n --help
```

### 3.2 LazyVim Integration
- [ ] Write Neovim plugin wrapper
- [ ] Integrate with `toggleterm.nvim` or `snacks.nvim`
- [ ] Floating terminal on `:Lazyi18n`
- [ ] Pass current project root automatically

**lazy.nvim spec** (`lazy-lazyi18n.lua`):
```lua
{
  "dir = '/path/to/lazyi18n',
  cmd = 'Lazyi18n',
  config = function()
    vim.keymap.set('n', '<leader>ti', ':Lazyi18n<CR>')
  end,
}
```

### 3.3 Configuration File
- [ ] Support `.lazyi18nrc` or config in project
- [ ] Configure: file patterns, indentation, locales
- [ ] Ignore certain directories/files

---

## 🎯 Quick Wins (Next Steps)

Pick one of these to unblock the others:

### A. Edit Mode (Unlocks all editing)
```python
# In ValuesPane, add when Enter is pressed:
- Show Input widgets for each locale
- Bind Ctrl+S to save values
- Bind Escape to cancel
- Update self.project with new values
```

**Impact**: Users can actually edit translations!

### B. Better Tree Navigation
```python
# Add to TreePane:
- Mouse click support (already in Textual)
- Double-click → Enter edit mode
- [x] 'd' → Delete key (with Enter/Escape confirmation)
```

**Impact**: Faster navigation and bulk operations

### C. Nicer Layout
```css
/* In LazyI18nApp.CSS, improve: */
- Colors for gaps (red), complete (green)
- Better spacing and borders
- Syntax highlighting for values
- Show file paths in header
```

**Impact**: Polish and professional appearance

---

## 🧪 Testing Strategy

### Unit Tests (43 tests passing ✅)
```python
tests/
├── test_loader.py      # File discovery & parsing
├── test_flatten.py     # Flatten/unflatten logic
├── test_analyzer.py    # Gap detection accuracy
├── test_writer.py      # File writing safety
└── test_project.py     # Integration tests
```

### Integration Tests
- Create temp dir with sample locales
- Load, modify, save
- Verify output matches expected

### Manual Testing
- `python3 test_core.py` → Core functionality
- `python3 main.py examples/` → UI in examples
- Test with your actual i18n files

---

## 📚 Learning Resources

- **Textual Docs**: https://textual.textualize.io/
  - Reactive attributes: https://textual.textualize.io/guide/reactivity/
  - CSS: https://textual.textualize.io/guide/CSS/
  - Widgets: https://textual.textualize.io/widget_gallery/

- **Rich Docs**: https://rich.readthedocs.io/
  - Console output, styling

- **i18next Format**: https://www.i18next.com/misc/json-format
  - Namespaces, pluralization, contexts

---

## 🏗️ Architecture Deep Dive

### Data Flow

```
Disk (JSON files)
    ↓
[TranslationFileLoader] → Load & parse JSON
    ↓
[TranslationProject] → Flatten & organize
    ├→ [TranslationGapAnalyzer] → Find gaps
    └→ [ValuesPane] → Display to user
    ↓
[Edit in UI]
    ↓
[TranslationProject.set_key_value()] → Track changes
    ↓
[User presses Ctrl+S]
    ↓
[TranslationWriter] → Unflatten & write atomically
    ↓
Disk (Updated JSON files)
```

### Key Design Principles

1. **Immutability during load**: Don't modify original until save
2. **Flat representation**: All comparison/display in dot-notation
3. **Atomic writes**: Never corrupt a file mid-write
4. **Change tracking**: Know what changed and why
5. **Reactive UI**: UI updates automatically with data changes

---

## 💪 Motivational Checkpoints

When you complete these milestones, celebrate! 🎉

- [x] **Phase 1 DONE**: Core engine works, test passes
- [ ] **Phase 2.3 DONE**: Can edit and save translations
- [ ] **Phase 2 DONE**: Full TUI with all features
- [ ] **Phase 3 DONE**: Integrated with LazyVim, ready to ship

---

## 🤔 FAQ & Troubleshooting

### Q: How do I add a new locale?
A: Drop a new JSON file in the directory, restart lazyi18n. It auto-detects.

### Q: What if my JSON has pluralization rules?
A: Currently supported (stored as objects). Display as `"key.plural"` in tree.

### Q: Can I sync with external translators?
A: Phase 4 feature—export/import CSV for translators, reimport results.

### Q: Performance on huge files?
A: Flattening is O(n). Rendering is lazy (Textual handles virtualization).
Test with 10k+ keys coming soon.

---

## 🎬 Getting Help

1. Check `test_core.py` for API usage examples
2. Read docstrings in `core/*.py`
3. Refer to Textual widget gallery for UI questions
4. Open an issue with the output of `python3 test_core.py`

---

**Last updated**: December 16, 2025
**Status**: Phase 1 ✅ | Phase 2 ✅ | Phase 3 📋
