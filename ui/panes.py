import re

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Input, Static, Tree
from textual.binding import Binding

from core.project import TranslationProject
from ui.icons import ICON_CHECK, ICON_CROSS, ICON_WARNING, ICON_PENCIL, ICON_FOLDER


def extract_interpolations(text: str | list | None) -> set[str]:
    """Extract {variable} and {{variable}} interpolation patterns from text."""
    if not text:
        return set()
    # Handle arrays (i18next supports arrays for plural forms, lists, etc.)
    if isinstance(text, list):
        result = set()
        for item in text:
            if isinstance(item, str):
                result.update(extract_interpolations(item))
        return result
    if not isinstance(text, str):
        return set()
    # Match {variable}, { variable }, {{variable}}, {{ variable }}, etc.
    # Uses a pattern that matches 1 or 2 braces on each side
    pattern = r"\{?\{\s*(\w+)\s*\}\}?"
    return set(re.findall(pattern, text))


def get_interpolation_issues(project: "TranslationProject") -> dict[str, list[str]]:
    """Get keys that have interpolation variable mismatches.

    Returns a dict mapping key -> list of locales with issues.
    """
    issues = {}
    locales = project.get_locales()
    if not locales:
        return issues

    source_locale = "en" if "en" in locales else locales[0]

    for key in project.get_all_keys():
        source_value = project.get_key_value(source_locale, key)
        source_vars = extract_interpolations(source_value)

        if not source_vars:
            continue

        key_issues = []
        for locale in locales:
            if locale == source_locale:
                continue
            target_value = project.get_key_value(locale, key)
            if not target_value:
                continue
            target_vars = extract_interpolations(target_value)
            if source_vars != target_vars:
                key_issues.append(locale)

        if key_issues:
            issues[key] = key_issues

    return issues


class TranslationTree(Tree):
    """Custom Tree widget to handle keybindings."""

    BINDINGS = [
        Binding("space", "app.edit", "Edit / Toggle"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
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
        interpolation_issues = get_interpolation_issues(self.project)

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
            has_interp_issue = key in interpolation_issues

            # Build interpolation warning suffix
            interp_warning = f" [{self.app.current_theme.warning}]{ICON_WARNING}[/]" if has_interp_issue else ""

            # Mark with status: unsaved, gap, or complete
            if has_unsaved:
                label = f"[{self.app.current_theme.warning}]{ICON_PENCIL}[/]  [bold {self.app.current_theme.warning}]{key}[/]{interp_warning}"
            elif has_gap:
                label = f"[{self.app.current_theme.error}]{ICON_CROSS}[/]  [bold {self.app.current_theme.error}]{key}[/]{interp_warning}"
            else:
                label = f"[{self.app.current_theme.success}]{ICON_CHECK}[/] {key}{interp_warning}"
            root.add_leaf(label, data=key)

        # Build tree with category warnings if any child has gaps or interpolation issues
        for category in sorted(categories.keys()):
            category_keys = categories[category]
            category_has_gap = any(k in gaps for k in category_keys)
            category_has_interp = any(k in interpolation_issues for k in category_keys)
            key_count = len(category_keys)

            # Calculate coverage for this category
            complete_keys = sum(1 for k in category_keys if k not in gaps)
            coverage_pct = (complete_keys / key_count * 100) if key_count > 0 else 100
            coverage_color = self.app.current_theme.success if coverage_pct == 100 else self.app.current_theme.warning if coverage_pct >= 80 else self.app.current_theme.error

            cat_label = f"[{self.app.current_theme.secondary}]{ICON_FOLDER}[/] {category} [dim]({key_count})[/] [{coverage_color}]{coverage_pct:.0f}%[/]"
            if category_has_gap:
                cat_label = f"[{self.app.current_theme.error}]{ICON_WARNING}[/] {cat_label}"
            elif category_has_interp:
                cat_label = f"[{self.app.current_theme.warning}]{ICON_WARNING}[/] {cat_label}"
            cat_node = root.add(cat_label)
            cat_node.expand()
            for key in sorted(categories[category]):
                label = key.split(".", 1)[1] if "." in key else key
                has_gap = key in gaps
                # Show pencil if this key has unsaved changes
                has_unsaved = key in changed_keys and unsaved_locales
                has_interp_issue = key in interpolation_issues

                # Build interpolation warning suffix
                interp_warning = f" [{self.app.current_theme.warning}]{ICON_WARNING}[/]" if has_interp_issue else ""

                # Mark with status: unsaved, gap, or complete
                if has_unsaved:
                    label = f"[{self.app.current_theme.warning}]{ICON_PENCIL}[/] [bold {self.app.current_theme.warning}]{label}[/]{interp_warning}"
                elif has_gap:
                    label = f"[{self.app.current_theme.error}]{ICON_CROSS}[/] [bold {self.app.current_theme.error}]{label}[/]{interp_warning}"
                else:
                    label = f"[{self.app.current_theme.success}]{ICON_CHECK}[/] {label}{interp_warning}"
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
                "Press [$secondary]?[/] for Help"
            )

        # Determine header color based on status
        header_color = "$primary"
        gaps = self.project.get_gaps()
        changed_keys = self.project.get_changed_keys()

        if self.selected_key in gaps:
            header_color = "$error"
        elif self.selected_key in changed_keys:
            header_color = "$warning"

        lines = [f"[bold {header_color} reverse] {self.selected_key} [/]\n"]

        # Determine source locale and extract its variables for comparison
        locales = self.project.get_locales()
        source_locale = "en" if "en" in locales else (locales[0] if locales else None)
        source_value = self.project.get_key_value(source_locale, self.selected_key) if source_locale else None
        source_vars = extract_interpolations(source_value) if source_value else set()

        for locale in locales:
            # Prefer preview values when editing this key
            if self.preview_key == self.selected_key and locale in self.preview_values:
                value = self.preview_values.get(locale) or ""
            else:
                value = self.project.get_key_value(locale, self.selected_key)

            if value:
                # Check for missing interpolation variables
                target_vars = extract_interpolations(value)
                missing_vars = source_vars - target_vars
                extra_vars = target_vars - source_vars

                warning = ""
                if missing_vars and locale != source_locale:
                    missing_str = ", ".join(sorted(missing_vars))
                    warning = f" [$warning]{ICON_WARNING} missing: {{{missing_str}}}[/]"
                elif extra_vars and locale != source_locale:
                    extra_str = ", ".join(sorted(extra_vars))
                    warning = f" [$warning]{ICON_WARNING} extra: {{{extra_str}}}[/]"

                lines.append(f"[$success]{ICON_CHECK} {locale}[/]: {value}{warning}")
            else:
                lines.append(f"[$error reverse]{ICON_CROSS} {locale} [/]: [dim]MISSING[/]")

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
        interpolation_issues = get_interpolation_issues(self.project)

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
            f"  Keys: [$primary]{total_keys}[/] | Locales: [$primary]{len(locales)}[/] ({', '.join(locales)})"
        )
        interp_info = ""
        if interpolation_issues:
            interp_info = f" | [$warning]{ICON_WARNING} {len(interpolation_issues)}[/] var issues"
        lines.append(
            f"  Fully Translated: [$success]{fully_translated}[/] | Partial: [$warning]{len(gaps)}[/]{interp_info}"
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
                color = (
                    "$success" if pct == 100 else "$warning" if pct >= 80 else "$error"
                )

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
                filters.append("[$warning]Edited (e)[/]")
            if self.show_missing:
                filters.append("[$error]Missing (m)[/]")
            lines.append(f"  [bold]Filters:[/] {', '.join(filters)}")
            lines.append("")

        # 3. System Status
        lines.append("[bold]System[/]")

        # Unsaved changes
        changed_keys = self.project.get_changed_keys()
        if changed_keys:
            lines.append(
                f"  [$warning]●[/] Unsaved Changes: [$warning]{len(changed_keys)}[/] keys modified"
            )
            lines.append(f"      Locales: {', '.join(self.unsaved)}")
        else:
            lines.append("  [$success]●[/] All changes saved")
        # Last Action
        if self.action != "Ready":
            lines.append(f"  [$secondary]ℹ[/] {self.action}")

        # Key hints (compact)
        lines.append("")
        lines.append("[dim]/:search n:new D:dup y:copy o:edit z/Z:fold s:save ?:help[/]")

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
