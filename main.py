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
from textual.containers import Horizontal, VerticalScroll, Container
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
                "  d  Delete selected key (with confirmation)",
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
        """Save all changes to memory and close."""
        # Read current values from inputs
        for locale, input_widget in self.inputs.items():
            # Get the text from the Input widget
            new_value = input_widget.value.strip() if input_widget.value else ""
            
            if new_value:
                self.project.set_key_value(locale, self.key, new_value)
            else:
                # Empty field deletes the translation for that locale
                self.project.delete_key_value(locale, self.key)
        
        # Update the values pane and tree immediately
        if hasattr(self.app, 'values_pane') and self.app.values_pane:
            self.app.values_pane.clear_preview()
            self.app.values_pane.refresh()
        
        if hasattr(self.app, 'tree_pane') and self.app.tree_pane:
            self.app.tree_pane.rebuild(self.app.tree_pane.search_term)
        
        if hasattr(self.app, 'status_pane') and self.app.status_pane:
            self.app.status_pane.update_status()
        
        # Close the modal
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel editing and close."""
        # Clear any live preview
        if hasattr(self.app, "values_pane") and self.app.values_pane:
            self.app.values_pane.clear_preview()
        self.app.pop_screen()


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
            self.error_label.update("[red][/] Key cannot be empty")
            return
        
        if not all(c.isalnum() or c in "._-" for c in key):
            self.error_label.update("[red][/] Key can only contain letters, numbers, dots, hyphens, and underscores")
            return
        
        # Check if key already exists
        if key in self.project.get_all_keys():
            self.error_label.update("[red][/] Key already exists")
            return
        
        # Collect values
        has_value = False
        for locale, input_widget in self.inputs.items():
            new_value = input_widget.value.strip()
            if new_value:
                has_value = True
                self.project.set_key_value(locale, key, new_value)
        
        if not has_value:
            self.error_label.update("[red][/] At least one translation must be provided")
            return
        
        # Notify main app to rebuild tree
        if hasattr(self.app, 'tree_pane'):
            self.app.tree_pane.rebuild(self.app.search_buffer if self.app.is_searching else "")
        if hasattr(self.app, 'status_pane'):
            self.app.status_pane.action = f"[green][/] Created key: {key}"
        
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
            self.error_label.update("[red][/] No missing translations to fill")
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
            self.error_label.update("[red][/] Provide at least one value to apply")
            return
        
        if hasattr(self.app, 'tree_pane'):
            self.app.tree_pane.rebuild(self.app.tree_pane.search_term)
        if hasattr(self.app, 'status_pane'):
            self.app.status_pane.action = "[green][/] Bulk applied"
        
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel bulk fill."""
        self.app.pop_screen()


class DeleteConfirmScreen(Screen):
    """Modal screen for confirming key deletion."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm Delete"),
    ]
    
    CSS = """
    DeleteConfirmScreen {
        align: center middle;
    }
    
    #delete-dialog {
        width: 60;
        height: auto;
        border: heavy $error;
        background: $surface;
        padding: 1 2;
    }
    
    #delete-title {
        text-align: center;
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #delete-key {
        color: $text;
        margin: 1 0;
        text-align: center;
    }
    
    #delete-warning {
        color: $text;
        margin: 1 0;
        text-align: center;
    }
    
    #delete-help {
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
    
    def compose(self) -> ComposeResult:
        """Compose the delete confirmation dialog."""
        with VerticalScroll(id="delete-dialog"):
            yield Label("Delete Translation Key?", id="delete-title")
            yield Label(f"[bold]{self.key}[/]", id="delete-key")
            yield Label(
                "This action cannot be undone. All translations for this key will be deleted.",
                id="delete-warning"
            )
            yield Label(
                "[bold green]Enter[/] Confirm | [Esc] Cancel",
                id="delete-help"
            )
    
    def action_confirm(self) -> None:
        """Confirm and delete the key from all locales."""
        # Delete the key from all locales
        for locale in self.project.get_locales():
            self.project.delete_key_value(locale, self.key)
        
        # Update the main app
        if hasattr(self.app, 'tree_pane'):
            self.app.tree_pane.rebuild(self.app.tree_pane.search_term)
        if hasattr(self.app, 'values_pane'):
            self.app.values_pane.selected_key = ""
        if hasattr(self.app, 'status_pane'):
            self.app.status_pane.action = f"[green][/] Deleted key: {self.key}"
            self.app.status_pane.update_status()
        
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel deletion."""
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
        unsaved_locales = self.project.get_unsaved_locales()
        changed_keys = self.project.get_changed_keys()
        
        # Filter keys by search term
        if filter_term:
            keys = [k for k in keys if filter_term.lower() in k.lower()]
        
        # Group by category (first part before dot) and identify top-level keys
        categories = {}
        top_level_keys = []  # Keys without dots
        
        for key in keys:
            if "." in key:
                parts = key.split(".")
                category = parts[0]
                if category not in categories:
                    categories[category] = []
                categories[category].append(key)
            else:
                top_level_keys.append(key)
        
        # Add top-level keys directly to root
        for key in sorted(top_level_keys):
            has_gap = key in gaps
            has_unsaved = key in changed_keys and unsaved_locales
            
            # Mark with status: unsaved, gap, or complete
            if has_unsaved:
                label = f"[yellow][/]  {key}"
            elif has_gap:
                label = f"[red][/]  {key}"
            else:
                label = f"[green][/] {key}"
            root.add_leaf(label, data=key)
        
        # Build tree with category warnings if any child has gaps
        for category in sorted(categories.keys()):
            category_keys = categories[category]
            category_has_gap = any(k in gaps for k in category_keys)
            cat_label = f"[blue][/] {category}"
            if category_has_gap:
                cat_label = f"[red][/]  {cat_label}"
            cat_node = root.add(cat_label)
            cat_node.expand()
            for key in sorted(categories[category]):
                label = key.split(".", 1)[1] if "." in key else key
                has_gap = key in gaps
                # Show pencil if this key has unsaved changes
                has_unsaved = key in changed_keys and unsaved_locales
                
                # Mark with status: unsaved, gap, or complete
                if has_unsaved:
                    label = f"[yellow][/]  {label}"
                elif has_gap:
                    label = f"[red][/]  {label}"
                else:
                    label = f"[green][/] {label}"
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
                lines.append(f"[green] {locale}[/green]: {value}")
            else:
                lines.append(f"[red] {locale}[/red]: [dim]MISSING[/]")
        
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


class StatusDisplay(Static):
    """Internal widget for displaying status text."""
    
    unsaved: reactive[list] = reactive([])
    action: reactive[str] = reactive("Ready")
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
    
    def render(self) -> str:
        """Render comprehensive status info."""
        coverage = self.project.get_coverage()
        gaps = self.project.get_gaps()
        total_keys = len(self.project.get_all_keys())
        missing_count = len(gaps)
        
        lines = [
            f"[bold cyan]Status[/]",
            f"  Keys: {total_keys} | Missing: {missing_count}",
        ]
        
        # Coverage per locale with progress bar
        if coverage:
            for locale, pct in sorted(coverage.items()):
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                lines.append(f"  {locale}: {bar} {pct:.0f}%")
        
        # Unsaved status
        if self.unsaved:
            unsaved_str = ", ".join(self.unsaved)
            lines.append(f"[yellow]  Unsaved:[/] {unsaved_str}")
        else:
            lines.append("[green] All saved[/]")
        
        # Action feedback
        if self.action != "Ready":
            lines.append(f"[dim]{self.action}[/]")
        
        # Key hints
        lines.append("")
        lines.append("[dim bold]Key Bindings[/]")
        lines.append("[dim]↑/↓ nav | e edit | / search | n new | b bulk | s save | r reload | ? help | q quit[/]")
        
        return "\n".join(lines)
    
    def update_status(self) -> None:
        """Update status from project."""
        self.unsaved = self.project.get_unsaved_locales()


class StatusPane(Container):
    """Bottom pane container showing status or search."""
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.display = StatusDisplay(project)
        self.search_input = Input(placeholder="Search keys...", id="search-input")
        self.search_input.display = False
        
        # Proxy properties to display widget for compatibility
        self._action = "Ready"
    
    @property
    def action(self):
        return self.display.action
        
    @action.setter
    def action(self, value):
        self.display.action = value
        
    def compose(self) -> ComposeResult:
        yield self.display
        yield self.search_input
        
    def update_status(self) -> None:
        self.display.update_status()


class LazyI18nApp(App):
    """Textual application for lazyi18n."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    Header {
        dock: top;
    }
    
    #left-pane {
        width: 40%;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #right-container {
        width: 60%;
        height: 1fr;
        layout: vertical;
    }
    
    #right-pane {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        padding: 1;
        overflow: auto;
    }
    
    #status-pane {
        width: 1fr;
        height: 50%;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }
    
    #search-input {
        border: none;
        background: $panel;
        width: 100%;
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
        ("d", "delete_key", "Delete"),
        ("escape", "cancel_search", "Cancel Search"),
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
        
        with Horizontal():
            self.tree_pane = TreePane(self.project)
            self.tree_pane.id = "left-pane"
            yield self.tree_pane
            
            with VerticalScroll(id="right-container"):
                self.values_pane = ValuesPane(self.project)
                self.values_pane.id = "right-pane"
                yield self.values_pane
                
                self.status_pane = StatusPane(self.project)
                self.status_pane.id = "status-pane"
                yield self.status_pane

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
        # Preserve Enter for Textual defaults; use 'e' to edit
        # Only trigger edit if we are NOT searching (Input widget handles its own keys)
        if not self.is_searching and event.key == "e" and self.values_pane.selected_key:
            self.action_edit()
    
    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_buffer = event.value
        self.tree_pane.rebuild(self.search_buffer)
    
    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        self.is_searching = False
        self.status_pane.search_input.display = False
        self.status_pane.display.display = True
        self.status_pane.action = f"Filter: {self.search_buffer or 'none'}"
        # Focus tree to allow navigation
        self.set_focus(self.tree_pane)
    
    def action_search(self) -> None:
        """Enter search mode."""
        self.is_searching = True
        self.status_pane.display.display = False
        self.status_pane.search_input.display = True
        self.status_pane.search_input.value = self.search_buffer
        self.set_focus(self.status_pane.search_input)
        
    def action_cancel_search(self) -> None:
        """Cancel search mode."""
        if self.is_searching:
            self.is_searching = False
            self.search_buffer = ""
            self.status_pane.search_input.display = False
            self.status_pane.display.display = True
            self.tree_pane.clear_filter()
            self.set_focus(self.tree_pane)
    
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
    
    def action_delete_key(self) -> None:
        """Delete the selected key with confirmation."""
        if self.values_pane.selected_key:
            self.push_screen(DeleteConfirmScreen(self.project, self.values_pane.selected_key))

    def action_save(self) -> None:
        """Save changes to disk and refresh UI."""
        if self.project.save():
            self.status_pane.action = "[green][/] Saved to disk"
            self.status_pane.update_status()
            # Rebuild tree to clear pencil indicators since everything is now saved
            self.tree_pane.rebuild(self.tree_pane.search_term)
            # Refresh values pane
            self.values_pane.refresh()
        else:
            self.status_pane.action = "[red][/] Save failed"
    
    def action_reload(self) -> None:
        """Reload from disk."""
        if self.project.reload():
            self.status_pane.action = "[green][/] Reloaded"
            self.status_pane.update_status()
            self.tree_pane.rebuild(self.tree_pane.search_term)
            self.values_pane.selected_key = ""
        else:
            self.status_pane.action = "[red][/] Reload failed"
    
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
