#!/usr/bin/env python3
"""
lazyi18n - A TUI for managing i18next translation files.

Enhanced version v3 with:
- Inline editing
- Single-key shortcuts
- Search/filter functionality
- New key creation wizard
"""

from pathlib import Path
import sys

from textual.app import App, ComposeResult
from textual import on
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Header, Static, Tree, Input, Label
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen

from core import TranslationProject
class HelpScreen(Screen):
    """Modal screen showing help and keybindings."""
    
    BINDINGS = [
        ("escape", "close", "Close"),
    ]
    
    CSS = """
    HelpScreen { align: center middle; }
    #help-dialog {
        width: 90;
        height: auto;
        max-height: 80%;
        border: heavy $accent;
        background: $surface;
        padding: 1 2;
    }
    #help-title { text-align: center; color: $accent; text-style: bold; margin-bottom: 1; }
    #help-body { color: $text; }
    #help-footer { dock: bottom; text-align: center; color: $text-muted; margin-top: 1; }
    """
    
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-dialog"):
            yield Label("LazyI18n Help", id="help-title")
            help_lines = [
                "[bold]Navigation[/]",
                "  ↑/↓  Move selection in left tree",
                "  /    Search/filter keys (type to filter; Esc cancels; Enter accepts)",
                "",
                "[bold]Editing[/]",
                "  e  Edit selected key",
                "  In editor: Tab/Enter next field; Ctrl+S save; Esc cancel; empty value deletes",
                "  Live preview updates in right pane while typing",
                "",
                "[bold]Keys[/]",
                "  n  Create a new key with per-locale values",
                "  b  Bulk fill missing translations per locale",
                "",
                "[bold]Project[/]",
                "  s  Save all changes to disk",
                "  r  Reload translations from disk",
                "  q  Quit",
            ]
            yield Label("\n".join(help_lines), id="help-body")
            yield Label("Press Esc to close", id="help-footer")
    
    def action_close(self) -> None:
        self.app.pop_screen()


class EditScreen(Screen):
    """Modal screen for editing translation values."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]
    
    CSS = """
    EditScreen {
        align: center middle;
    }
    
    #edit-dialog {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    #edit-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .locale-label {
        margin-top: 1;
        color: $text-muted;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    #edit-help {
        dock: bottom;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """
    
    def __init__(self, project: TranslationProject, key: str):
        super().__init__()
        self.project = project
        self.key = key
        self.inputs = {}
        self.input_order = []
    
    def compose(self) -> ComposeResult:
        """Compose the edit dialog."""
        with VerticalScroll(id="edit-dialog"):
            yield Label(f"Edit: {self.key}", id="edit-title")
            
            for locale in self.project.get_locales():
                yield Label(f"{locale}:", classes="locale-label")
                current_value = self.project.get_key_value(locale, self.key) or ""
                input_widget = Input(
                    value=current_value,
                    placeholder=f"Enter {locale} translation..."
                )
                # Track inputs by locale via self.inputs dict
                self.inputs[locale] = input_widget
                self.input_order.append(input_widget)
                yield input_widget
            
            yield Label(
                "[Esc] Cancel | [Ctrl+S] Save | [Tab/Enter] Next field | Empty value = delete",
                id="edit-help"
            )

    def on_mount(self) -> None:
        """Focus the first input on open."""
        if self.input_order:
            self.set_focus(self.input_order[0])

    def on_key(self, event) -> None:
        """Handle Enter to move to the next field without clearing text."""
        if event.key == "enter" and self.input_order:
            try:
                current = self.focused
                idx = self.input_order.index(current) if current in self.input_order else -1
                next_idx = (idx + 1) % len(self.input_order)
                self.set_focus(self.input_order[next_idx])
                event.stop()
                return
            except ValueError:
                pass
    
    def action_save(self) -> None:
        """Save all changes and close."""
        for locale, input_widget in self.inputs.items():
            new_value = input_widget.value.strip()
            if new_value:
                self.project.set_key_value(locale, self.key, new_value)
            else:
                # Empty field deletes the translation for that locale
                self.project.delete_key_value(locale, self.key)
        # Clear any live preview
        if hasattr(self.app, "values_pane") and self.app.values_pane:
            self.app.values_pane.clear_preview()
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel editing and close."""
        # Clear any live preview
        if hasattr(self.app, "values_pane") and self.app.values_pane:
            self.app.values_pane.clear_preview()
        self.app.pop_screen()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update live preview in the values pane while editing."""
        # Collect current input values per locale
        current_values = {}
        for locale, input_widget in self.inputs.items():
            val = (input_widget.value or "").strip()
            current_values[locale] = val
        # Push preview to ValuesPane
        if hasattr(self.app, "values_pane") and self.app.values_pane:
            self.app.values_pane.set_preview(self.key, current_values)


class NewKeyScreen(Screen):
    """Modal screen for creating new translation keys."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "create", "Create"),
    ]
    
    CSS = """
    NewKeyScreen {
        align: center middle;
    }
    
    #new-key-dialog {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    
    #new-key-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .key-label {
        margin-top: 1;
        color: $text-muted;
    }
    
    #key-input {
        margin-bottom: 2;
    }
    
    .locale-label {
        margin-top: 1;
        color: $text-muted;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    #new-key-help {
        dock: bottom;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    
    #error-message {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    """
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.key_input = None
        self.inputs = {}
        self.error_label = None
    
    def compose(self) -> ComposeResult:
        """Compose the new key dialog."""
        with VerticalScroll(id="new-key-dialog"):
            yield Label("Create New Translation Key", id="new-key-title")
            
            yield Label("Key (e.g., auth.login.title):", classes="key-label")
            self.key_input = Input(
                placeholder="Enter key path...",
                id="key-input"
            )
            yield self.key_input
            
            for locale in self.project.get_locales():
                yield Label(f"{locale}:", classes="locale-label")
                input_widget = Input(
                    placeholder=f"Enter {locale} translation..."
                )
                # Track inputs by locale via self.inputs dict
                self.inputs[locale] = input_widget
                yield input_widget
            
            self.error_label = Label("", id="error-message")
            yield self.error_label
            
            yield Label(
                "[Esc] Cancel | [Ctrl+S] Create | [Tab] Next field",
                id="new-key-help"
            )
    
    def action_create(self) -> None:
        """Create the new key."""
        key = self.key_input.value.strip()
        
        # Validate key
        if not key:
            self.error_label.update("❌ Key cannot be empty")
            return
        
        if not all(c.isalnum() or c in "._-" for c in key):
            self.error_label.update("❌ Key can only contain letters, numbers, dots, hyphens, and underscores")
            return
        
        # Check if key already exists
        if key in self.project.get_all_keys():
            self.error_label.update("❌ Key already exists")
            return
        
        # Collect values
        has_value = False
        for locale, input_widget in self.inputs.items():
            new_value = input_widget.value.strip()
            if new_value:
                has_value = True
                self.project.set_key_value(locale, key, new_value)
        
        if not has_value:
            self.error_label.update("❌ At least one translation must be provided")
            return
        
        # Notify main app to rebuild tree
        if hasattr(self.app, 'tree_pane'):
            self.app.tree_pane.rebuild(self.app.search_buffer if self.app.is_searching else "")
        if hasattr(self.app, 'status_pane'):
            self.app.status_pane.action = f"✓ Created key: {key}"
        
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel creating new key."""
        self.app.pop_screen()


class BulkFillScreen(Screen):
    """Modal screen for bulk filling missing translations."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "apply", "Apply"),
    ]
    
    CSS = """
    BulkFillScreen {
        align: center middle;
    }
    
    #bulk-dialog {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    
    #bulk-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .locale-label {
        margin-top: 1;
        color: $text-muted;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    #bulk-help {
        dock: bottom;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    
    #bulk-missing {
        color: $text-muted;
        margin-top: 1;
    }
    
    #error-message {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    """
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.inputs = {}
        self.error_label = None
        self.missing_keys = []
        self.missing_by_locale = {}
    
    def compose(self) -> ComposeResult:
        """Compose the bulk fill dialog."""
        gaps = self.project.get_gaps()
        self.missing_keys = sorted(gaps.keys())
        self.missing_by_locale = {locale: [] for locale in self.project.get_locales()}
        for key, gap in gaps.items():
            for locale in gap.missing_in:
                self.missing_by_locale[locale].append(key)
        
        with VerticalScroll(id="bulk-dialog"):
            yield Label("Bulk Fill Missing Translations", id="bulk-title")
            
            # Show missing summary
            summary_lines = ["Missing keys:"]
            for locale, keys in self.missing_by_locale.items():
                summary_lines.append(f"  {locale}: {len(keys)} missing")
            missing_text = "\n".join(summary_lines)
            yield Label(missing_text, id="bulk-missing")
            
            for locale in self.project.get_locales():
                yield Label(f"Fill for {locale} (optional):", classes="locale-label")
                input_widget = Input(
                    placeholder=f"Enter value to apply to {len(self.missing_by_locale.get(locale, []))} missing keys..."
                )
                # Track inputs by locale via self.inputs dict
                self.inputs[locale] = input_widget
                yield input_widget
            
            self.error_label = Label("", id="error-message")
            yield self.error_label
            
            yield Label(
                "[Esc] Cancel | [Ctrl+S] Apply to missing keys",
                id="bulk-help"
            )
    
    def action_apply(self) -> None:
        """Apply bulk fill to missing translations."""
        if not self.missing_keys:
            self.error_label.update("❌ No missing translations to fill")
            return
        
        any_value = False
        for locale, input_widget in self.inputs.items():
            val = input_widget.value.strip()
            if not val:
                continue
            any_value = True
            for key in self.missing_by_locale.get(locale, []):
                self.project.set_key_value(locale, key, val)
        
        if not any_value:
            self.error_label.update("❌ Provide at least one value to apply")
            return
        
        if hasattr(self.app, 'tree_pane'):
            self.app.tree_pane.rebuild(self.app.tree_pane.search_term)
        if hasattr(self.app, 'status_pane'):
            self.app.status_pane.action = "✓ Bulk applied"
        
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel bulk fill."""
        self.app.pop_screen()


class TreePane(Static):
    """Left pane with translation key tree."""
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self._tree = None
        self.search_term = ""
    
    def compose(self) -> ComposeResult:
        """Compose the tree pane."""
        self._tree = Tree("Keys")
        self._tree.root.expand()
        self._build_tree()
        yield self._tree
    
    def _build_tree(self, filter_term: str = "") -> None:
        """Build the tree from translation keys."""
        if not self._tree:
            return
        
        root = self._tree.root
        root.data = None
        gaps = self.project.get_gaps()
        keys = self.project.get_all_keys()
        
        # Filter keys by search term
        if filter_term:
            keys = [k for k in keys if filter_term.lower() in k.lower()]
        
        # Group by category
        categories = {}
        for key in keys:
            parts = key.split(".")
            category = parts[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        # Build tree with category warnings if any child has gaps
        for category in sorted(categories.keys()):
            category_keys = categories[category]
            category_has_gap = any(k in gaps for k in category_keys)
            cat_label = f"📁 {category}"
            if category_has_gap:
                cat_label = f"⚠️  {cat_label}"
            cat_node = root.add(cat_label)
            cat_node.expand()
            for key in sorted(categories[category]):
                label = key.split(".", 1)[1] if "." in key else key
                has_gap = key in gaps
                if has_gap:
                    label = f"⚠️  {label}"
                else:
                    label = f"✓ {label}"
                cat_node.add_leaf(label, data=key)
    
    def rebuild(self, filter_term: str = "") -> None:
        """Rebuild the tree."""
        self.search_term = filter_term
        if self._tree:
            self._tree.clear()
            self._tree.root.expand()
            self._build_tree(filter_term)
    
    def clear_filter(self) -> None:
        """Clear search filter."""
        self.search_term = ""
        self.rebuild("")


class ValuesPane(Static):
    """Right pane showing translation values."""
    
    selected_key: reactive[str] = reactive("", recompose=True)
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.preview_key = ""
        self.preview_values = {}
    
    def render(self) -> str:
        """Render values for selected key."""
        if not self.selected_key:
            return (
                "[dim]Select a key from the tree[/]\n\n"
                "[bold]Keyboard Shortcuts:[/]\n"
                "  [cyan]↑/↓[/]   Navigate tree\n"
                "  [cyan]e[/]     Edit translations\n"
                "  [cyan]/[/]     Search/filter\n"
                "  [cyan]n[/]     New key\n"
                "  [cyan]b[/]     Bulk fill missing\n"
                "  [cyan]s[/]     Save changes\n"
                "  [cyan]r[/]     Reload from disk\n"
                "  [cyan]q[/]     Quit\n"
                "  [cyan]?[/]     Help\n"
            )
        
        lines = [f"[bold cyan]{self.selected_key}[/]\n"]
        
        for locale in self.project.get_locales():
            # Prefer preview values when editing this key
            if self.preview_key == self.selected_key and locale in self.preview_values:
                value = self.preview_values.get(locale) or ""
            else:
                value = self.project.get_key_value(locale, self.selected_key)
            if value:
                lines.append(f"[green]✓ {locale}[/green]: {value}")
            else:
                lines.append(f"[red]✗ {locale}[/red]: [dim]MISSING[/]")
        
        lines.append("")
        lines.append("[dim italic]Press e to edit[/]")
        
        return "\n".join(lines)

    def set_preview(self, key: str, values: dict) -> None:
        """Set live preview values for a key and refresh display."""
        self.preview_key = key or ""
        self.preview_values = values or {}
        self.refresh()

    def clear_preview(self) -> None:
        """Clear any live preview and refresh display."""
        self.preview_key = ""
        self.preview_values = {}
        self.refresh()


class StatusPane(Static):
    """Bottom pane showing status."""
    
    unsaved: reactive[list] = reactive([])
    action: reactive[str] = reactive("Ready")
    search_mode: reactive[bool] = reactive(False)
    search_term: reactive[str] = reactive("")
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
    
    def render(self) -> str:
        """Render status bar."""
        hints_line = (
            "[dim]Keys: ↑/↓ navigate | e edit | / search | n new | b bulk | s save | r reload | ? help | q quit[/]"
        )
        if self.search_mode:
            return (
                f"[bold yellow]SEARCH:[/] {self.search_term}_ | [dim]ESC to cancel | ENTER to finish[/]" 
                + "\n" + hints_line
            )
        
        coverage = self.project.get_coverage()
        coverage_str = " | ".join(
            f"{l}: {c:.0f}%" for l, c in coverage.items()
        )
        unsaved_str = ", ".join(self.unsaved) if self.unsaved else "none"
        
        status_line = (
            f"Coverage: {coverage_str} | "
            f"Unsaved: {unsaved_str} | "
            f"Action: {self.action}"
        )
        return status_line + "\n" + hints_line
    
    def update_status(self) -> None:
        """Update status from project."""
        self.unsaved = self.project.get_unsaved_locales()


class LazyI18nApp(App):
    """Textual application for lazyi18n."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    Header {
        dock: top;
    }
    
    Footer {
        dock: bottom;
    }
    
    #left-pane {
        width: 40%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-pane {
        width: 60%;
        border: solid $primary;
        padding: 1;
    }
    
    #status-pane {
        dock: bottom;
        height: 5;
        border: solid $accent;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("s", "save", "Save"),
        ("q", "quit", "Quit"),
        ("r", "reload", "Reload"),
        ("?", "help", "Help"),
        ("e", "edit", "Edit"),
        ("/", "search", "Search"),
        ("n", "new_key", "New Key"),
        ("b", "bulk_fill", "Bulk Fill"),
    ]
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.tree_pane = None
        self.values_pane = None
        self.status_pane = None
        self.search_buffer = ""
        self.is_searching = False
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        
        self.status_pane = StatusPane(self.project)
        self.status_pane.id = "status-pane"
        yield self.status_pane
        
        with Horizontal():
            self.tree_pane = TreePane(self.project)
            self.tree_pane.id = "left-pane"
            yield self.tree_pane
            
            self.values_pane = ValuesPane(self.project)
            self.values_pane.id = "right-pane"
            yield self.values_pane
        
        # Footer removed to avoid overlapping the status pane

    def on_mount(self) -> None:
        """Initialize status contents after UI mounts."""
        if self.status_pane:
            self.status_pane.action = "Ready"
            self.status_pane.update_status()
    
    @on(Tree.NodeSelected)
    def on_tree_select(self, event: Tree.NodeSelected) -> None:
        """Handle tree selection."""
        if event.node.data:
            self.values_pane.selected_key = event.node.data
            # Force refresh to ensure right pane updates immediately
            self.values_pane.refresh()

    @on(Tree.NodeHighlighted)
    def on_tree_highlight(self, event: Tree.NodeHighlighted) -> None:
        """Update values pane when the highlighted node changes via navigation."""
        if event.node.data:
            self.values_pane.selected_key = event.node.data
            # Force refresh to ensure right pane updates during navigation
            self.values_pane.refresh()
    
    def on_key(self, event) -> None:
        """Handle keyboard input."""
        # Handle search mode
        if self.is_searching:
            if event.key == "escape":
                # Cancel search
                self.is_searching = False
                self.search_buffer = ""
                self.status_pane.search_mode = False
                self.tree_pane.clear_filter()
                return
            elif event.key == "enter":
                # Finish search
                self.is_searching = False
                self.status_pane.search_mode = False
                self.status_pane.action = f"Filter: {self.search_buffer or 'none'}"
                return
            elif event.key == "backspace":
                # Delete character
                self.search_buffer = self.search_buffer[:-1]
                self.status_pane.search_term = self.search_buffer
                self.tree_pane.rebuild(self.search_buffer)
                return
            elif len(event.key) == 1 and event.key.isprintable():
                # Add character
                self.search_buffer += event.key
                self.status_pane.search_term = self.search_buffer
                self.tree_pane.rebuild(self.search_buffer)
                return
        
        # Preserve Enter for Textual defaults; use 'e' to edit
        if event.key == "e" and self.values_pane.selected_key:
            self.action_edit()
    
    def action_search(self) -> None:
        """Enter search mode."""
        self.is_searching = True
        self.search_buffer = ""
        self.status_pane.search_mode = True
        self.status_pane.search_term = ""
    
    def action_edit(self) -> None:
        """Edit the selected key."""
        if self.values_pane.selected_key:
            self.push_screen(EditScreen(self.project, self.values_pane.selected_key))
    
    def action_new_key(self) -> None:
        """Create a new translation key."""
        self.push_screen(NewKeyScreen(self.project))
    
    def action_bulk_fill(self) -> None:
        """Bulk fill missing translations."""
        self.push_screen(BulkFillScreen(self.project))

    def action_save(self) -> None:
        """Save changes to disk."""
        if self.project.save():
            self.status_pane.action = "✓ Saved"
            self.status_pane.update_status()
            self.tree_pane.rebuild(self.tree_pane.search_term)
        else:
            self.status_pane.action = "✗ Save failed"
    
    def action_reload(self) -> None:
        """Reload from disk."""
        if self.project.reload():
            self.status_pane.action = "✓ Reloaded"
            self.status_pane.update_status()
            self.tree_pane.rebuild(self.tree_pane.search_term)
            self.values_pane.selected_key = ""
        else:
            self.status_pane.action = "✗ Reload failed"
    
    def action_help(self) -> None:
        """Show help modal."""
        self.push_screen(HelpScreen())


class LazyI18nTUI:
    """Main TUI wrapper."""
    
    def __init__(self, directory: Path | str = "."):
        self.directory = Path(directory)
        self.project = TranslationProject(self.directory)
    
    def load(self) -> bool:
        """Load translations from disk."""
        return self.project.load()
    
    def create_app(self) -> LazyI18nApp:
        """Create and return the Textual app."""
        return LazyI18nApp(self.project)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="lazyi18n - TUI for managing i18next translations"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to directory with translation files (default: current directory)",
    )
    
    args = parser.parse_args()
    
    tui = LazyI18nTUI(args.directory)
    
    if not tui.load():
        print("Error: Failed to load translations from", args.directory)
        sys.exit(1)
    
    app = tui.create_app()
    app.run()


if __name__ == "__main__":
    main()
