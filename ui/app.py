"""
Textual UI for lazyi18n - Main application.
"""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree
from textual.reactive import reactive

from core import TranslationProject


class TranslationTree(Tree):
    """Custom tree widget for displaying translation keys."""
    
    def __init__(self, project: TranslationProject):
        super().__init__("Root")
        self.project = project
        self._build_tree()
    
    def _build_tree(self) -> None:
        """Build the tree from translation keys."""
        root = self.root
        root.label = "Keys"
        
        # Group keys by first level
        keys = self.project.get_all_keys()
        gaps = self.project.get_gaps()
        
        # Build hierarchy
        categories = {}
        for key in keys:
            parts = key.split(".")
            category = parts[0] if len(parts) > 1 else "other"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        # Add to tree
        for category in sorted(categories.keys()):
            node = root.add(category)
            for key in sorted(categories[category]):
                label = key
                # Mark gaps with a warning emoji
                if key in gaps:
                    label += " ⚠️"
                node.add_leaf(label, data=key)


class ValuesPanel(Static):
    """Right pane showing translation values for selected key."""
    
    selected_key: reactive[Optional[str]] = reactive(None, recompose=True)
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
    
    def render(self) -> str:
        """Render the values panel."""
        if not self.selected_key:
            return "[dim]Select a key to view translations[/]"
        
        lines = [f"[bold]{self.selected_key}[/]", ""]
        
        for locale in self.project.get_locales():
            value = self.project.get_key_value(locale, self.selected_key)
            status = "✓" if value else "✗ Missing"
            if value:
                lines.append(f"[green]{locale}[/] {status}: {value}")
            else:
                lines.append(f"[red]{locale}[/] {status}")
        
        return "\n".join(lines)


class StatusBar(Static):
    """Bottom pane showing status and recent actions."""
    
    unsaved_count: reactive[int] = reactive(0)
    last_action: reactive[str] = reactive("Ready")
    
    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.update_status()
    
    def render(self) -> str:
        """Render the status bar."""
        coverage = self.project.get_coverage()
        coverage_str = ", ".join(
            f"{loc}: {cov:.1f}%" for loc, cov in coverage.items()
        )
        
        return (
            f"[bold]Coverage:[/] {coverage_str} | "
            f"[bold]Unsaved:[/] {self.unsaved_count} | "
            f"[bold]Action:[/] {self.last_action}"
        )
    
    def update_status(self) -> None:
        """Update status from project."""
        self.unsaved_count = len(self.project.get_unsaved_locales())


class LazyI18nApp:
    """Main application using Textual."""
    
    def __init__(self, directory: Path | str):
        self.project = TranslationProject(directory)
    
    def load(self) -> bool:
        """Load project from disk."""
        return self.project.load()
    
    def save(self) -> bool:
        """Save all changes."""
        return self.project.save()
