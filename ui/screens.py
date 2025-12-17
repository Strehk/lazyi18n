from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Input, Label

from core.project import TranslationProject


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

    def on_mount(self) -> None:
        """Focus key input on mount."""
        self.set_focus(self.key_input)
    
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


class QuitConfirmScreen(Screen):
    """Modal screen for confirming quit with unsaved changes."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]
    
    CSS = """
    QuitConfirmScreen {
        align: center middle;
        background: $background 80%;
    }
    
    #quit-dialog {
        width: 60;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 2;
    }
    
    #quit-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $error;
    }
    
    #quit-warning {
        color: $text;
        margin: 1 0;
        text-align: center;
    }
    
    #quit-help {
        dock: bottom;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the quit confirmation dialog."""
        with VerticalScroll(id="quit-dialog"):
            yield Label("Unsaved Changes", id="quit-title")
            yield Label(
                "You have unsaved changes. Are you sure you want to quit?",
                id="quit-warning"
            )
            yield Label(
                "[bold red]Enter[/] Quit without saving | [Esc] Cancel",
                id="quit-help"
            )
    
    def action_confirm(self) -> None:
        """Confirm quit."""
        self.app.exit()
    
    def action_cancel(self) -> None:
        """Cancel quit."""
        self.app.pop_screen()


class ReloadConfirmScreen(Screen):
    """Modal screen for confirming reload with unsaved changes."""
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]
    
    CSS = """
    ReloadConfirmScreen {
        align: center middle;
        background: $background 80%;
    }
    
    #reload-dialog {
        width: 60;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 2;
    }
    
    #reload-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $error;
    }
    
    #reload-warning {
        color: $text;
        margin: 1 0;
        text-align: center;
    }
    
    #reload-help {
        dock: bottom;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the reload confirmation dialog."""
        with VerticalScroll(id="reload-dialog"):
            yield Label("Unsaved Changes", id="reload-title")
            yield Label(
                "You have unsaved changes. Reloading will discard them.",
                id="reload-warning"
            )
            yield Label(
                "[bold red]Enter[/] Reload and discard | [Esc] Cancel",
                id="reload-help"
            )
    
    def action_confirm(self) -> None:
        """Confirm reload."""
        self.app.pop_screen()
        self.app.perform_reload()
    
    def action_cancel(self) -> None:
        """Cancel reload."""
        self.app.pop_screen()
