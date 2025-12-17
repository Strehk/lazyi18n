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

Where lazyi18n truly begins to shine is its integration with Neovim, especially when using LazyVim. You can open lazyi18n in a floating terminal window directly from your editor, even directly going to the edit mode for what is currently under your cursor. It makes managing and especially creating translations a breeze.

There are 1000s of ways to set this up and I highly recommend adapting it to your own workflow and files, but here is my configuration to get you started. I am using `snacks.nvim` in my LazyVim setup, but you could achieve similar results with `toggleterm.nvim` or any other terminal plugin.

<details>
<summary>### Opening lazyi18n in Neovim</summary>

```lua
return {
  {
    "folke/snacks.nvim",
    optional = true,
    keys = {
      {
        "<leader>tt", -- I have this setup under tt like lazygit (gg)
        function()
          local lazyi18n_path = vim.fn.exepath("lazyi18n")

          local command = string.format("%s", lazyi18n_path)

          Snacks.terminal(command, {
            win = {
              position = "float",
              border = "rounded",
              width = 0.9,
              height = 0.9,
            },
          })
        end,
        desc = "Open lazyi18n",
      },
    },
  },
}
```

</details>

<details>
<summary>### Opening lazyi18n in edit mode for the key under the cursor</summary>

```lua
return {
  {
    "folke/snacks.nvim",
    optional = true,
    keys = {
      {
        "<leader>te", -- I have this setup under te like translate edit
        function()
          -- Get the current line text
          local line = vim.api.nvim_get_current_line()
          -- Get the cursor position (1-based row, 0-based col)
          local col = vim.api.nvim_win_get_cursor(0)[2]

          -- This pattern looks for:
          -- 1. Optional characters ending in a dot (prefix like 'm.' or 't.')
          -- 2. Captures everything non-paren until a '('
          -- The %b() match is powerful but simple pattern matching is safer here for cursor context.

          -- Strategy: Find the full string "prefix.key.chain(" around the cursor
          -- We expand <cWORD> first to get a rough context, usually grabs "m.auth.title("
          local cWORD = vim.fn.expand("<cWORD>")

          -- Extract what is inside the dots and parens
          -- Pattern explanation:
          -- ^.-%. : Match start, any char, until a literal dot (removes m.)
          -- (.-)  : Capture everything
          -- %($   : Until the literal open parenthesis at the end
          local key = cWORD:match("^.-%.(.-)%($")

          -- Fallback: If cWORD has trailing chars like "m.key()," stripping trailing chars
          if not key then
            key = cWORD:match("^.-%.([%w_%.]+)")
          end

          -- Validate we actually have a key worth adding
          if not key or key == "" then
            vim.notify("Could not detect a valid translation key under cursor.", vim.log.levels.WARN)
            return
          end

          local lazyi18n_path = vim.fn.exepath("lazyi18n")

          if lazyi18n_path == "" then
            vim.notify("lazyi18n executable not found", vim.log.levels.ERROR)
            return
          end

          -- Construct the specific command: lazyi18n --edit <key>
          -- Note: Your snippet used --edit, so I kept that.
          -- If you wanted --new as per your first message, swap it back!
          local command = string.format("%s --edit %s", lazyi18n_path, key)

          vim.notify("Editing key: " .. key, vim.log.levels.INFO)

          Snacks.terminal(command, {
            win = {
              position = "float",
              border = "rounded",
              width = 0.9,
              height = 0.9,
            },
            interactive = true, -- Keep it open so you can save/edit in the TUI
          })
        end,
        desc = "Add or edit i18n key under cursor",
      },
    },
  },
}
```

</details>

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
