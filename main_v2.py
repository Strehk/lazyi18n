#!/usr/bin/env python3
"""
lazyi18n - A TUI for managing i18next translation files.

Main entry point with full Textual application.
"""

from pathlib import Path
import sys

from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree
from textual.reactive import reactive
from textual.binding import Binding

from core import TranslationProject


class TreePane(Static):
    """Left pane with translation key tree."""
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self._tree = None
    
    def compose(self) -> ComposeResult:
        """Compose the tree pane."""
        self._tree = Tree("Keys")
        self._tree.root.expand()
        self._build_tree()
        yield self._tree
    
    def _build_tree(self) -> None:
        """Build the tree from translation keys."""
        if not self._tree:
            return
        
        root = self._tree.root
        gaps = self.project.get_gaps()
        keys = self.project.get_all_keys()
        
        # Group by category
        categories = {}
        for key in keys:
            parts = key.split(".")
            category = parts[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        # Build tree
        for category in sorted(categories.keys()):
            cat_node = root.add(f"📁 {category}")
            for key in sorted(categories[category]):
                label = key.split(".", 1)[1] if "." in key else key
                has_gap = key in gaps
                if has_gap:
                    label = f"⚠️  {label}"
                cat_node.add_leaf(label, data=key)


class ValuesPane(Static):
    """Right pane showing translation values."""
    
    selected_key: reactive[str] = reactive("")
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
    
    def render(self) -> str:
        """Render values for selected key."""
        if not self.selected_key:
            return "[dim]Select a key from the tree[/]"
        
        lines = [f"[bold cyan]{self.selected_key}[/]\n"]
        
        for locale in self.project.get_locales():
            value = self.project.get_key_value(locale, self.selected_key)
            if value:
                lines.append(f"[green]{locale}[/green]: {value}")
            else:
                lines.append(f"[red]{locale}[/red]: [dim]MISSING[/]")
        
        return "\n".join(lines)


class StatusPane(Static):
    """Bottom pane showing status."""
    
    unsaved: reactive[list] = reactive([])
    action: reactive[str] = reactive("Ready")
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
    
    def render(self) -> str:
        """Render status bar."""
        coverage = self.project.get_coverage()
        coverage_str = " | ".join(
            f"{l}: {c:.0f}%" for l, c in coverage.items()
        )
        unsaved_str = ", ".join(self.unsaved) if self.unsaved else "none"
        
        return (
            f"Coverage: {coverage_str} | "
            f"Unsaved: {unsaved_str} | "
            f"Action: {self.action}"
        )
    
    def update_status(self) -> None:
        """Update status from project."""
        self.unsaved = self.project.get_unsaved_locales()


class LazyI18nTUI:
    """Main TUI application."""
    
    def __init__(self, directory: Path | str = "."):
        self.directory = Path(directory)
        self.project = TranslationProject(self.directory)
    
    def load(self) -> bool:
        """Load translations from disk."""
        return self.project.load()
    
    def create_app(self) -> "LazyI18nApp":
        """Create and return the Textual app."""
        from textual.app import App
        
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
                height: 3;
                border: solid $accent;
                padding: 1;
            }
            """
            
            BINDINGS = [
                Binding("ctrl+s", "save", "Save", show=True),
                Binding("ctrl+q", "quit", "Quit", show=True),
                Binding("ctrl+r", "reload", "Reload", show=True),
                ("?", "help", "Help"),
            ]
            
            def __init__(self, project: TranslationProject):
                super().__init__()
                self.project = project
                self.tree_pane = None
                self.values_pane = None
                self.status_pane = None
            
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
                
                yield Footer()
            
            @on(Tree.NodeSelected)
            def on_tree_select(self, event: Tree.NodeSelected) -> None:
                """Handle tree selection."""
                if event.node.data:
                    self.values_pane.selected_key = event.node.data
            
            def action_save(self) -> None:
                """Save changes to disk."""
                if self.project.save():
                    self.status_pane.action = "✓ Saved"
                    self.status_pane.update_status()
                else:
                    self.status_pane.action = "✗ Save failed"
            
            def action_reload(self) -> None:
                """Reload from disk."""
                if self.project.reload():
                    self.status_pane.action = "✓ Reloaded"
                    # Rebuild tree
                    self.tree_pane._build_tree()
                else:
                    self.status_pane.action = "✗ Reload failed"
            
            def action_help(self) -> None:
                """Show help."""
                self.status_pane.action = "Commands: Ctrl+S save, Ctrl+R reload, Ctrl+Q quit"
        
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
