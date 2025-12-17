# 🎉 lazyi18n v3.0 - RELEASE NOTES

## What's New in Version 3.0

### Major Features

#### 🔍 Advanced Search & Filter
Press **/** to enter search mode. Now supports searching both **Keys** and **Values**!
- Type to filter the tree in real-time.
- Matches against translation keys (e.g., `auth.login`).
- Matches against translation values (e.g., "Sign In").
- Press **Enter** to lock the filter.
- Press **Esc** to clear.

#### 📊 Dashboard & Statistics
The status bar has been replaced with a comprehensive Dashboard:
- **Total Keys**: Count of all translation keys.
- **Missing**: Count of missing translations across all locales.
- **Coverage**: Percentage of completion per locale (e.g., `en: 100%`, `de: 85%`).
- **Visual Indicators**: Green for complete, Red for missing.

#### 🛡️ Safety First
No more accidental data loss!
- **Quit Confirmation**: Pressing **q** with unsaved changes now prompts for confirmation.
- **Reload Confirmation**: Pressing **r** with unsaved changes now prompts for confirmation.

#### ✨ UI Polish
A complete visual overhaul:
- **Rounded Borders**: Modern look for all panels.
- **Titles**: Clear titles for "Navigation", "Values", and "Dashboard".
- **Transparency**: Removed background colors for a cleaner integration with your terminal theme.
- **Focus**: Input fields now auto-focus for smoother workflow.
- **Key Highlighting**: The currently selected key path is displayed prominently.

#### 🆕 Key Creation Wizard
Press **n** to create a new translation key:
- Modal dialog to enter the key path.
- Input fields for all locales.
- Validation to prevent duplicates.

### Removed Features

#### 🗑️ Bulk Fill
The "Bulk Fill" feature has been removed to focus on precision and quality. We believe translations should be done carefully, not in bulk with placeholder text.

## Migration Guide

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| **/** | Search (Keys & Values) |
| **n** | Create New Key |
| **q** | Quit (with safety check) |
| **r** | Reload (with safety check) |
| **e** | Edit Key |

### Configuration
No changes to your JSON files. They remain 100% compatible.

## New Files in v3.0

- `RELEASE_NOTES_v3.0.md` (This file)
- Updated `main.py` with new UI components.
