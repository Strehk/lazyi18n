from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Input, Static, Tree
from textual.binding import Binding

from core.project import TranslationProject


class TranslationTree(Tree):
    """Custom Tree widget to handle keybindings."""

    BINDINGS = [
        Binding("space", "app.edit", "Edit / Toggle"),
    ]


class TreePane(Static):
    """Left pane with translation key tree."""

    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self._tree = None
        self.search_term = ""
        self.border_title = "Keys"

    def compose(self) -> ComposeResult:
        """Compose the tree pane."""
        self._tree = TranslationTree("Keys")
        self._tree.root.expand()
        self._build_tree()
        yield self._tree

    def _build_tree(
        self,
        filter_term: str = "",
        show_staged: bool = False,
        show_missing: bool = False,
    ) -> None:
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
            term = filter_term.lower()
            filtered_keys = []
            for key in keys:
                # Check key match
                if term in key.lower():
                    filtered_keys.append(key)
                    continue

                # Check value match in any locale
                for locale in self.project.get_locales():
                    val = self.project.get_key_value(locale, key)
                    if val and term in str(val).lower():
                        filtered_keys.append(key)
                        break
            keys = filtered_keys

        # Filter by staged/missing
        if show_staged or show_missing:
            filtered_keys = []
            for key in keys:
                is_staged = key in changed_keys
                is_missing = key in gaps

                if show_staged and show_missing:
                    if is_staged or is_missing:
                        filtered_keys.append(key)
                elif show_staged and is_staged:
                    filtered_keys.append(key)
                elif show_missing and is_missing:
                    filtered_keys.append(key)
            keys = filtered_keys

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
                label = f"[yellow][/]  [bold yellow]{key}[/]"
            elif has_gap:
                label = f"[red][/]  [bold red]{key}[/]"
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
                    label = f"[yellow][/]  [bold yellow]{label}[/]"
                elif has_gap:
                    label = f"[red][/]  [bold red]{label}[/]"
                else:
                    label = f"[green][/] {label}"
                cat_node.add_leaf(label, data=key)

    def rebuild(
        self,
        filter_term: str = "",
        show_staged: bool = False,
        show_missing: bool = False,
    ) -> None:
        """Rebuild the tree."""
        self.search_term = filter_term
        if self._tree:
            self._tree.clear()
            self._tree.root.expand()
            self._build_tree(filter_term, show_staged, show_missing)

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
        self.border_title = "Translations"

    def render(self) -> str:
        """Render values for selected key."""
        if not self.selected_key:
            return (
                "[$primary] #                           ###   #    #####         \n"
                " #         ##   ###### #   #  #   ##   #     # #    # \n"
                " #        #  #      #   # #   #  # #   #     # ##   # \n"
                " #       #    #    #     #    #    #    #####  # #  # \n"
                " #       ######   #      #    #    #   #     # #  # # \n"
                " #       #    #  #       #    #    #   #     # #   ## \n"
                " ####### #    # ######   #   ### #####  #####  #    # \n[/]"
                "\n\n"
                "[dim]Select a key from the tree[/]\n\n"
                "Press [cyan]?[/] for Help"
            )

        lines = [f"[bold cyan reverse] {self.selected_key} [/]\n"]

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
    show_staged: reactive[bool] = reactive(False)
    show_missing: reactive[bool] = reactive(False)

    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project

    def render(self) -> str:
        """Render comprehensive status info."""
        coverage = self.project.get_coverage()
        gaps = self.project.get_gaps()
        all_keys = self.project.get_all_keys()
        total_keys = len(all_keys)
        locales = self.project.get_locales()

        # Calculate stats
        fully_translated = total_keys - len(gaps)

        # Calculate missing per locale
        missing_per_locale = {loc: 0 for loc in locales}
        for gap in gaps.values():
            for loc in gap.missing_in:
                missing_per_locale[loc] += 1

        lines = []

        # 1. Project Overview
        lines.append("[bold]Project Overview[/]")
        lines.append(
            f"  Keys: [cyan]{total_keys}[/] | Locales: [cyan]{len(locales)}[/] ({', '.join(locales)})"
        )
        lines.append(
            f"  Fully Translated: [green]{fully_translated}[/] | Partial: [yellow]{len(gaps)}[/]"
        )
        lines.append("")

        # 2. Locale Health
        lines.append("[bold]Locale Health[/]")
        if coverage:
            for locale in locales:
                pct = coverage.get(locale, 0)
                missing = missing_per_locale.get(locale, 0)
                present = total_keys - missing

                # Color based on percentage
                color = "green" if pct == 100 else "yellow" if pct >= 80 else "red"

                # Progress bar (20 chars wide)
                bar_width = 20
                filled = int(pct / 100 * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)

                lines.append(
                    f"  {locale:<5} [{color}]{bar}[/] {pct:>5.1f}%  ([dim]{present}/{total_keys}[/])"
                )
        lines.append("")

        # Active Filters
        if self.show_staged or self.show_missing:
            filters = []
            if self.show_staged:
                filters.append("[yellow]Edited (e)[/]")
            if self.show_missing:
                filters.append("[red]Missing (m)[/]")
            lines.append(f"  [bold]Filters:[/] {', '.join(filters)}")
            lines.append("")

        # 3. System Status
        lines.append("[bold]System[/]")

        # Unsaved changes
        changed_keys = self.project.get_changed_keys()
        if changed_keys:
            lines.append(
                f"  [yellow]●[/] Unsaved Changes: [yellow]{len(changed_keys)}[/] keys modified"
            )
            lines.append(f"      Locales: {', '.join(self.unsaved)}")
        else:
            lines.append("  [green]●[/] All changes saved")

        # Last Action
        if self.action != "Ready":
            lines.append(f"  [blue]ℹ[/] {self.action}")

        # Key hints (compact)
        lines.append("")
        lines.append("[dim]e:edit /:search n:new s:save r:reload q:quit[/]")

        return "\n".join(lines)

    def update_status(self) -> None:
        """Update status from project."""
        self.unsaved = self.project.get_unsaved_locales()


class StatusPane(Container):
    """Bottom pane container showing status or search."""

    def __init__(self, project: TranslationProject):
        super().__init__()
        self.project = project
        self.status_display = StatusDisplay(project)
        self.search_input = Input(placeholder="Search keys...", id="search-input")
        self.search_input.display = False
        self.border_title = "Status"

        # Proxy properties to display widget for compatibility
        self._action = "Ready"

    @property
    def action(self):
        return self.status_display.action

    @action.setter
    def action(self, value):
        self.status_display.action = value

    def compose(self) -> ComposeResult:
        yield self.status_display
        yield self.search_input

    def update_status(self) -> None:
        self.status_display.update_status()

    def update_filters(self, show_staged: bool, show_missing: bool) -> None:
        self.status_display.show_staged = show_staged
        self.status_display.show_missing = show_missing
