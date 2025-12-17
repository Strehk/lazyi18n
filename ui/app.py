from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.theme import Theme
from textual.widgets import Header, Input, Tree

from core.project import TranslationProject
from core.config import Config
from core.translator import Translator, TranslationError
from core.llm import LLMTranslator
from ui.panes import StatusPane, TreePane, ValuesPane
from ui.screens import (
    DeleteConfirmScreen,
    EditScreen,
    HelpScreen,
    NewKeyScreen,
    QuitConfirmScreen,
    ReloadConfirmScreen,
    LoadingScreen,
    LLMConfirmScreen,
    LLMMissingKeyScreen,
    LLMProgressScreen,
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
        ("t", "translate_key", "Translate Key"),
        ("a", "llm_translate", "LLM Translate"),
        ("T", "translate_all_missing", "Translate All Missing"),
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
        
        # Initialize config and translator
        self.config = Config(Path(project.directory))
        # Google Translate (deep-translator) does not require an API key
        self.translator = Translator()

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

    def _load_theme(self) -> None:
        """Load and register theme from config."""
        # Check if a specific built-in theme is requested
        theme_name = self.config.get("theme.name", "textual-dark")
        
        # Check for custom color overrides
        primary = self.config.get("theme.primary")
        secondary = self.config.get("theme.secondary")
        accent = self.config.get("theme.accent")
        warning = self.config.get("theme.warning")
        error = self.config.get("theme.error")
        success = self.config.get("theme.success")
        
        if any([primary, secondary, accent, warning, error, success]):
            # Create a custom theme based on the requested name (if possible) or default
            custom_theme = Theme(
                name="lazyi18n-custom",
                primary=primary or "#004578", # Default textual-dark primary
                secondary=secondary or "#005a9e",
                accent=accent or "#0078d4",
                warning=warning or "#ffa500",
                error=error or "#ff0000",
                success=success or "#008000",
                dark=self.config.get("theme.dark", True)
            )
            self.register_theme(custom_theme)
            self.theme = "lazyi18n-custom"
        elif theme_name:
            # Just use the named theme (built-in)
            self.theme = theme_name

    def on_mount(self) -> None:
        """Initialize status contents after UI mounts."""
        self._load_theme() 
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

    def action_translate_key(self) -> None:
        """Translate the selected key for all missing locales."""
        if self.is_searching:
            return
        
        if not self.values_pane.selected_key:
            self.status_pane.action = f"[$warning]⚠[/] No key selected"
            self.status_pane.update_status()
            return

        key = self.values_pane.selected_key
        
        try:
            # Translate missing locales for this key
            translations = self.translator.translate_missing(self.project, key)
            
            if not translations:
                self.status_pane.action = f"[$secondary]ℹ[/] No missing translations for {key}"
                self.status_pane.update_status()
                return
            
            # Apply translations (stages them, doesn't save)
            for locale, text in translations.items():
                self.project.set_key_value(locale, key, text)
            
            count = len(translations)
            self.status_pane.action = f"[$success][/] Translated {key} to {count} locale(s)"
            self.status_pane.update_status()
            
            # Refresh UI
            self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)
            self.values_pane.refresh()
            
        except TranslationError as e:
            self.status_pane.action = f"[$error]✗[/] Translation failed: {e}"
            self.status_pane.update_status()

    def action_llm_translate(self) -> None:
        """Translate the selected key using LLM."""
        if self.is_searching:
            return
        
        if not self.values_pane.selected_key:
            self.status_pane.action = f"[$warning]⚠[/] No key selected"
            self.status_pane.update_status()
            return

        key = self.values_pane.selected_key
        
        # Get source text (from default locale)
        locales = self.project.get_locales()
        if not locales:
             return
             
        # Simple heuristic: use 'en' if present, else first locale
        source_locale = 'en' if 'en' in locales else locales[0]
        source_text = self.project.get_key_value(source_locale, key)
        
        if not source_text:
             self.status_pane.action = f"[$warning]⚠[/] No source text found for {key} in {source_locale}"
             self.status_pane.update_status()
             return

        # Determine target locales (missing ones)
        target_locales = []
        for locale in locales:
            if locale == source_locale:
                continue
            if not self.project.get_key_value(locale, key):
                target_locales.append(locale)
        
        if not target_locales:
             self.status_pane.action = f"[$warning]ℹ[/] No missing translations for {key}"
             self.status_pane.update_status()
             return

        # Initialize LLM Translator to get config
        try:
            config = Config(self.project.directory)
            api_key = config.get("openai.api_key")
            
            if not api_key:
                self.push_screen(LLMMissingKeyScreen())
                return

            llm_translator = LLMTranslator(
                api_key=api_key,
                base_url=config.get("openai.base_url"),
                model=config.get("openai.model", "gpt-3.5-turbo"),
            )
        except Exception as e:
             self.status_pane.action = f"[$warning]✗[/] LLM Init failed: {e}"
             self.status_pane.update_status()
             return

        def do_translate():
            # Create and push progress screen
            progress_screen = LLMProgressScreen()
            self.push_screen(progress_screen)
            
            self.status_pane.action = f"[$warning]⏳[/] LLM Translating {key}..."
            self.status_pane.update_status()
            
            # Pass the function reference, not the result of calling it
            self.run_worker(
                lambda: self._llm_translate_worker(llm_translator, key, source_locale, source_text, target_locales, progress_screen), 
                thread=True
            )

        self.push_screen(LLMConfirmScreen(
            key=key,
            source_locale=source_locale,
            source_text=source_text,
            target_locales=target_locales,
            model=llm_translator.model,
            on_confirm=do_translate
        ))

    def _llm_translate_worker(self, translator, key, source_locale, source_text, target_locales, progress_screen) -> None:
        def log_callback(msg: str):
            self.call_from_thread(progress_screen.write_log, msg)

        try:
            translations = translator.translate_key(
                key, 
                source_text, 
                source_locale, 
                target_locales,
                log_callback=log_callback
            )
            self.call_from_thread(self._on_llm_translate_complete, key, translations, None)
        except Exception as e:
            self.call_from_thread(self._on_llm_translate_complete, key, None, str(e))

    def _on_llm_translate_complete(self, key: str, translations: dict | None, error: str | None) -> None:
        self.pop_screen() # Remove progress screen
        
        if error:
            self.status_pane.action = f"[$error]✗[/] LLM Translation failed: {error}"
            self.status_pane.update_status()
            return
        
        if not translations:
             self.status_pane.action = f"[$secondary]ℹ[/] No translations returned for {key}"
             self.status_pane.update_status()
             return

        # Apply translations
        for locale, text in translations.items():
            self.project.set_key_value(locale, key, text)
        
        count = len(translations)
        self.status_pane.action = f"[$success][/] LLM Translated {key} to {count} locale(s)"
        self.status_pane.update_status()
        
        # Refresh UI
        self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)
        self.values_pane.refresh()

    def action_translate_all_missing(self) -> None:
        """Translate all missing keys across all locales."""
        if self.is_searching:
            return
        
        gaps = self.project.get_gaps()
        if not gaps:
            self.status_pane.action = f"[$secondary]ℹ[/] No missing translations"
            self.status_pane.update_status()
            return
        
        self.status_pane.action = f"[$warning]⏳[/] Translating all missing keys..."
        self.status_pane.update_status()
        
        # Run translation in background worker
        self.run_worker(self._translate_all_worker, thread=True)

    def _translate_all_worker(self) -> None:
        """Background worker for translating all missing keys."""
        try:
            translations = self.translator.translate_all_missing(self.project)
            self.call_from_thread(self._on_translate_all_complete, translations, None)
        except Exception as e:
            self.call_from_thread(self._on_translate_all_complete, None, str(e))

    def _on_translate_all_complete(self, translations: dict | None, error: str | None) -> None:
        """Handle completion of translate all operation."""
        if error:
            self.status_pane.action = f"[$error]✗[/] Translation failed: {error}"
            self.status_pane.update_status()
            return
        
        if not translations:
            self.status_pane.action = f"[$secondary]ℹ[/] No translations generated"
            self.status_pane.update_status()
            return
        
        # Apply translations (stages them, doesn't save)
        for (locale, key), text in translations.items():
            self.project.set_key_value(locale, key, text)
        
        count = len(translations)
        self.status_pane.action = f"[$success][/] Translated {count} missing keys"
        self.status_pane.update_status()
        
        # Refresh UI
        self.tree_pane.rebuild(self.search_buffer, self.show_staged, self.show_missing)
        self.values_pane.refresh()

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
            self.status_pane.action = f"[$success][/] Saved to disk"
            self.status_pane.update_status()
            # Rebuild tree to clear pencil indicators since everything is now saved
            self.tree_pane.rebuild(
                self.search_buffer, self.show_staged, self.show_missing
            )
            # Refresh values pane
            self.values_pane.refresh()
        else:
            self.status_pane.action = f"[$error][/] Save failed"

    def perform_reload(self) -> None:
        """Execute the reload operation."""
        if self.project.reload():
            self.status_pane.action = f"[$success][/] Reloaded"
            self.status_pane.update_status()
            self.tree_pane.rebuild(
                self.search_buffer, self.show_staged, self.show_missing
            )
            self.values_pane.selected_key = ""
        else:
            self.status_pane.action = f"[$error][/] Reload failed"

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
