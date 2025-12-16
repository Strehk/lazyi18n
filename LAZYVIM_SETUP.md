# lazyi18n + LazyVim Integration Guide

Getting lazyi18n running in your LazyVim setup for a seamless TUI workflow.

## Prerequisites

- macOS with Homebrew (or equivalent package manager)
- Neovim (v0.9+) with LazyVim configured
- Python 3.8+
- Git

## Installation Steps

### 1. Clone lazyi18n

```bash
# Clone to a convenient location
git clone https://github.com/yourusername/lazyi18n.git ~/.local/share/lazyi18n

# Or develop locally
cd ~/Developer/lazyi18n
```

### 2. Install Dependencies

```bash
cd ~/.local/share/lazyi18n
pip3 install -r requirements.txt

# Verify installation
python3 test_core.py
```

### 3. Create a Bash Wrapper Script

This makes `lazyi18n` callable from anywhere (like lazygit).

Create `~/.local/bin/lazyi18n`:

```bash
#!/bin/bash
exec python3 ~/.local/share/lazyi18n/main.py "$@"
```

Make it executable:
```bash
chmod +x ~/.local/bin/lazyi18n
```

Add to your shell PATH (in `~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Now test:
```bash
lazyi18n ~/.local/share/lazyi18n/examples
```

### 4. LazyVim Plugin Setup

Create `~/.config/nvim/lua/plugins/lazyi18n.lua`:

```lua
return {
  {
    "not-a-real-plugin/lazyi18n",  -- placeholder key
    cmd = "Lazyi18n",
    config = function()
      -- Create custom command
      vim.api.nvim_create_user_command("Lazyi18n", function(opts)
        local dir = opts.args or vim.fn.getcwd()
        
        -- Use toggleterm or snacks to open floating terminal
        require("lazyi18n").open(dir)
      end, {
        nargs = "?",
        complete = "dir",
      })
    end,
  },
}
```

Then add to `~/.config/nvim/lua/plugins/toggleterm.lua` (if not already configured):

```lua
return {
  "akinsho/toggleterm.nvim",
  -- ... existing config ...
}
```

And create `~/.config/nvim/lua/lazyi18n.lua`:

```lua
local M = {}

function M.open(dir)
  local Terminal = require("toggleterm.terminal").Terminal
  local lazyi18n = Terminal:new({
    cmd = "lazyi18n " .. dir,
    direction = "float",
    hidden = true,
  })
  lazyi18n:toggle()
end

return M
```

### 5. Create Keybinding

Add to `~/.config/nvim/init.lua` or `~/.config/nvim/lua/config/keymaps.lua`:

```lua
vim.keymap.set("n", "<leader>ti", function()
  -- Get project root (assumes you're using lspconfig or other method)
  local root = vim.fn.getcwd()
  vim.cmd("terminal lazyi18n " .. root)
end, { noremap = true, silent = true, desc = "Open lazyi18n" })
```

Or use snacks.nvim if you prefer (it's in cutting-edge LazyVim):

```lua
-- In your snacks config
return {
  {
    "folke/snacks.nvim",
    opts = {
      terminal = {
        win = { position = "float" },
      },
    },
  },
}
```

Then in init.lua:
```lua
vim.keymap.set("n", "<leader>ti", function()
  Snacks.terminal("lazyi18n " .. vim.fn.getcwd(), { 
    cwd = vim.fn.getcwd() 
  })
end, { noremap = true, silent = true })
```

## Quick Test

Once installed, test the integration:

```bash
# In a directory with i18n files
cd ~/my-project/locales
lazyi18n .

# Or from Neovim
:Lazyi18n
```

You should see:
- Left pane: Tree of translation keys
- Right pane: Values for selected key
- Bottom: Coverage stats and unsaved changes

## Directory Structure

After installation, your setup looks like:

```
~/.local/
├── bin/
│   └── lazyi18n          # Executable script
└── share/
    └── lazyi18n/         # Source code
        ├── core/
        ├── main.py
        ├── requirements.txt
        └── examples/

~/.config/nvim/
└── lua/
    ├── plugins/
    │   └── lazyi18n.lua  # Plugin config
    └── lazyi18n.lua      # Helper module
```

## Usage in Neovim

### Opening lazyi18n

```vim
" From command line (after setup)
:Lazyi18n

" Or with explicit path
:Lazyi18n ~/my-project/locales
```

### Within lazyi18n TUI

```
Ctrl+S       → Save all changes
Ctrl+Q       → Close and return to Neovim
Ctrl+R       → Reload from disk
Arrow Keys   → Navigate tree
Enter        → Select key (future: edit)
?            → Show help
```

### Integration Tips

1. **Use in a float**: Set toggleterm to float mode for best experience
2. **Hotkey**: Bind to `<leader>ti` (translation i18n) for quick access
3. **Project detection**: Point to i18n directory, not project root
4. **Quick return**: Ctrl+Q exits cleanly back to Vim

## Troubleshooting

### Command not found: lazyi18n
```bash
# Check PATH
echo $PATH

# Check if binary is executable
ls -la ~/.local/bin/lazyi18n

# Verify installation
python3 -c "from core import TranslationProject"
```

### Neovim command not found: Lazyi18n
```bash
# Reload Neovim config
:source ~/.config/nvim/init.lua
:Lazyi18n
```

### Python module not found
```bash
# Ensure dependencies are installed in the right Python
~/.local/share/lazyi18n/requirements.txt

pip3 install -r ~/.local/share/lazyi18n/requirements.txt
```

### Terminal opens but TUI doesn't display
```bash
# Test directly
lazyi18n ~/.local/share/lazyi18n/examples

# Should show the TUI. If it doesn't:
# - Check Textual is installed: pip3 show textual
# - Verify terminal supports ANSI colors
```

## Advanced: Custom Configuration

Create `~/.lazyi18nrc` (future feature):

```json
{
  "locales_pattern": "locales/*.json",
  "indent": 2,
  "ignore_keys": ["system.*"],
  "auto_backup": true
}
```

## Updates

To stay up-to-date with lazyi18n:

```bash
cd ~/.local/share/lazyi18n
git pull origin main
pip3 install -r requirements.txt  # In case deps changed
```

## Next Steps

- [ ] Test the TUI with your own i18n files
- [ ] Try editing translations (Phase 2.3)
- [ ] Set up custom keybindings in Nvim
- [ ] Contribute improvements back!

---

**Questions?** Check [CHECKLIST.md](CHECKLIST.md) or open an issue.
