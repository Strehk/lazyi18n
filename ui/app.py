from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Header, Input, Tree

from core.project import TranslationProject
from ui.panes import StatusPane, TreePane, ValuesPane
from ui.screens import (
    DeleteConfirmScreen,
    EditScreen,
    HelpScreen,
    NewKeyScreen,
    QuitConfirmScreen,
    ReloadConfirmScreen,
    LoadingScreen,
)


class LazyI18nApp(App):
    """Textual application for lazyi18n."""

    TITLE = "LazyI18n"

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
        border: round $primary;
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
        border: round $primary;
        padding: 1;
        overflow: auto;
    }
    
    #status-pane {
        width: 1fr;
        height: 50%;
        border: round $accent;
        padding: 1;
    }
    
    #search-input {
        border: none;
        width: 100%;
        background: transparent;
    }
    
    Tree {
        background: transparent;
    }
    """

    BINDINGS = [
        ("s", "save", "Save"),
        ("q", "quit", "Quit"),
        ("r", "reload", "Reload"),
        ("?", "help", "Help"),
        ("space", "edit", "Edit"),
        ("/", "search", "Search"),
        ("n", "new_key", "New Key"),
        ("d", "delete_key", "Delete"),
        ("e", "toggle_staged", "Toggle Edited Filter"),
        ("m", "toggle_missing", "Toggle Missing Filter"),
        ("escape", "cancel_search", "Cancel Search"),
    ]

    def __init__(self, project: TranslationProject, initial_key: str | None = None):
        super().__init__()
        self.project = project
        self.initial_key = initial_key
        self.tree_pane = None
        self.values_pane = None
        self.status_pane = None
        self.search_buffer = ""
        self.is_searching = False
        self.show_staged = False
        self.show_missing = False

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

        # Show loading screen and start loading
        self.push_screen(LoadingScreen())
        self.run_worker(self.load_project, thread=True)

    def load_project(self) -> None:
        """Load the project in a background thread."""
        success = self.project.load()
        self.call_from_thread(self.on_project_loaded, success)

    def on_project_loaded(self, success: bool) -> None:
        """Handle project load completion."""
        self.pop_screen()  # Remove loading screen

        if not success:
            self.notify("Failed to load translations", severity="error")
            return

        # Rebuild tree now that data is loaded
        if self.tree_pane:
            self.tree_pane.rebuild()

        if self.initial_key:
            all_keys = self.project.get_all_keys()
            if self.initial_key in all_keys:
                self.push_screen(EditScreen(self.project, self.initial_key))
            else:
                self.push_screen(
                    NewKeyScreen(self.project, initial_key=self.initial_key)
                )

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

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_buffer = event.value
        self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        self.is_searching = False
        self.status_pane.search_input.display = False
        self.status_pane.status_display.display = True
        self.status_pane.action = f"Filter: {self.search_buffer or 'none'}"
        # Focus tree to allow navigation
        self.set_focus(self.tree_pane)

    def action_toggle_staged(self) -> None:
        """Toggle staged keys filter."""
        if self.is_searching:
            return
        self.show_staged = not self.show_staged
        self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)
        self.status_pane.update_filters(self.show_staged, self.show_missing)

    def action_toggle_missing(self) -> None:
        """Toggle missing keys filter."""
        if self.is_searching:
            return
        self.show_missing = not self.show_missing
        self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)
        self.status_pane.update_filters(self.show_staged, self.show_missing)

    def action_search(self) -> None:
        """Enter search mode."""
        self.is_searching = True
        self.status_pane.status_display.display = False
        self.status_pane.search_input.display = True
        self.status_pane.search_input.value = self.search_buffer
        self.set_focus(self.status_pane.search_input)

    def action_cancel_search(self) -> None:
        """Cancel search mode."""
        if self.is_searching:
            self.is_searching = False
            self.search_buffer = ""
            self.status_pane.search_input.display = False
            self.status_pane.status_display.display = True
            self.tree_pane.clear_filter()
            self.set_focus(self.tree_pane)

    def action_edit(self) -> None:
        """Edit the selected key or toggle branch expansion."""
        if self.is_searching:
            return

        # If we are on a branch node (no data), toggle expansion
        # We need to access the tree widget directly
        if self.tree_pane and hasattr(self.tree_pane, "_tree"):
            node = self.tree_pane._tree.cursor_node
            if node and node.allow_expand:
                node.toggle()
                return

        if self.values_pane.selected_key:
            self.push_screen(EditScreen(self.project, self.values_pane.selected_key))

    def action_new_key(self) -> None:
        """Create a new translation key."""
        if self.is_searching:
            return
        self.push_screen(NewKeyScreen(self.project))

    def action_delete_key(self) -> None:
        """Delete the selected key with confirmation."""
        if self.is_searching:
            return
        if self.values_pane.selected_key:
            self.push_screen(
                DeleteConfirmScreen(self.project, self.values_pane.selected_key)
            )

    def action_quit(self) -> None:
        """Quit the application."""
        if self.is_searching:
            return

        if self.project.has_unsaved_changes():
            self.push_screen(QuitConfirmScreen())
        else:
            self.exit()

    def action_save(self) -> None:
        """Save changes to disk and refresh UI."""
        if self.is_searching:
            return
        if self.project.save():
            self.status_pane.action = "[green][/] Saved to disk"
            self.status_pane.update_status()
            # Rebuild tree to clear pencil indicators since everything is now saved
            self.tree_pane.rebuild(
                self.search_buffer, self.show_staged, self.show_missing
            )
            # Refresh values pane
            self.values_pane.refresh()
        else:
            self.status_pane.action = "[red][/] Save failed"

    def perform_reload(self) -> None:
        """Execute the reload operation."""
        if self.project.reload():
            self.status_pane.action = "[green][/] Reloaded"
            self.status_pane.update_status()
            self.tree_pane.rebuild(
                self.search_buffer, self.show_staged, self.show_missing
            )
            self.values_pane.selected_key = ""
        else:
            self.status_pane.action = "[red][/] Reload failed"

    def action_reload(self) -> None:
        """Reload from disk."""
        if self.is_searching:
            return

        if self.project.has_unsaved_changes():
            self.push_screen(ReloadConfirmScreen())
        else:
            self.perform_reload()

    def action_help(self) -> None:
        """Show help modal."""
        if self.is_searching:
            return
        self.push_screen(HelpScreen())


class LazyI18nTUI:
    """Main TUI wrapper."""

    def __init__(self, directory: Path | str = ".", initial_key: str | None = None):
        self.directory = Path(directory)
        self.project = TranslationProject(self.directory)
        self.initial_key = initial_key

    def load(self) -> bool:
        """Load translations from disk."""
        return self.project.load()

    def create_app(self) -> LazyI18nApp:
        """Create and return the Textual app."""
        return LazyI18nApp(self.project, initial_key=self.initial_key)
