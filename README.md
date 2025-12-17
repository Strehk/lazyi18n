# lazyI18n

A terminal UI for managing i18next translation files, inspired by lazygit. Wrangle your nested JSON translation files with ease, identify missing translations at a glance, and maintain consistency across locales.

## Why lazyi18n?

Editing i18n files manually is painful:
- **No useful integration in your editor workflow**
- **Missing translations** are hard to spot
- **Nested JSON** is awkward to navigate
- **Manual comparison** between locales is tedious

lazyi18n brings the UX of lazygit to translation management. It's a TUI that helps you:
- **Visualize translation keys** in a tree structure
- **Highlight gaps** in translations across locales
- **Integrate with LazyVim/Neovim** for seamless workflow

## Installation

### Homebrew (macOS/Linux)

The easiest way to install is via Homebrew.

**Stable Release:**
```bash
brew tap strehk/lazyi18n
brew install lazyi18n
```

**Nightly Build:**
```bash
brew tap strehk/lazyi18n
brew install lazyi18n-nightly
```

### Manual Installation

You can download the latest release from the [Releases page](https://github.com/Strehk/lazyi18n/releases).

1. Download the `.tar.gz` or `.whl` file.
2. Install via pip:
   ```bash
   pip install lazyi18n-x.y.z.tar.gz
   ```

### From Source

```bash
git clone https://github.com/Strehk/lazyi18n
cd lazyi18n
pip install -e .
```

## Usage

### CLI

Run `lazyi18n` in your terminal. By default, it looks for translation files in the current directory.

```bash
# Open in current directory
lazyi18n

# Open in a specific directory
lazyi18n ./locales

# Open directly in edit mode for a specific key
# If the key exists, it opens the editor.
# If the key is missing, it opens the creation dialog with the key prefilled.
lazyi18n -e auth.login.title
```

### Keybindings

Press `?` within the application to see the full list of keybindings.

## Neovim Integration

You can integrate `lazyi18n` directly into Neovim using `toggleterm.nvim` or `snacks.nvim`.

### Using `snacks.nvim` (Recommended for LazyVim)

Add this to your `lua/plugins/lazyi18n.lua`:

```lua
return {
  {
    "folke/snacks.nvim",
    opts = {
      terminal = {
        win = {
          style = "lazyi18n",
        },
      },
      styles = {
        lazyi18n = {
          width = 0.9,
          height = 0.9,
          border = "rounded",
          title = " lazyi18n ",
          title_pos = "center",
          ft = "lazyi18n",
        },
      },
    },
    keys = {
      {
        "<leader>ti",
        function()
          Snacks.terminal("lazyi18n", { style = "lazyi18n" })
        end,
        desc = "Open lazyi18n",
      },
    },
  },
}
```

### Using `toggleterm.nvim`

```lua
return {
  {
    "akinsho/toggleterm.nvim",
    keys = {
      {
        "<leader>ti",
        function()
          local Terminal = require("toggleterm.terminal").Terminal
          local lazyi18n = Terminal:new({
            cmd = "lazyi18n",
            direction = "float",
            float_opts = {
              border = "curved",
              width = math.floor(vim.o.columns * 0.9),
              height = math.floor(vim.o.lines * 0.9),
            },
          })
          lazyi18n:toggle()
        end,
        desc = "Open lazyi18n",
      },
    },
  },
}
```

## Usage

Run `lazyi18n` in your project directory containing translation files:

```bash
lazyi18n [path/to/locales]
```

If no path is provided, it defaults to the current directory.

### Keybindings

- **Navigation**: `j`/`k` or `Up`/`Down`
- **Expand/Collapse**: `Space` or `Enter`
- **Edit Value**: `e` (on a leaf node)
- **Save**: `Ctrl+s`
- **Quit**: `q` or `Ctrl+c`

## Contributing

Contributions are welcome! Please follow these steps:

1.  **Fork the repository**.
2.  **Create a branch** for your feature or fix.
3.  **Install dev dependencies**:
    ```bash
    pip install -e .[dev]
    ```
4.  **Run tests and linter**:
    ```bash
    pytest
    ruff check .
    ```
5.  **Submit a Pull Request**.

Please ensure your code passes all tests and linting checks.

## License

MIT License. See [LICENSE](LICENSE) for details.
