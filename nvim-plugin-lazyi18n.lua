-- lazyi18n.lua
-- LazyVim plugin configuration for lazyi18n
-- Install: Copy to ~/.config/nvim/lua/plugins/lazyi18n.lua

return {
  {
    "akinsho/toggleterm.nvim",
    optional = true,
    keys = {
      {
        "<leader>ti",
        function()
          local lazyi18n_path = vim.fn.expand("~/.local/share/lazyi18n/lazyi18n.sh")
          local cwd = vim.fn.getcwd()
          
          -- Check if lazyi18n.sh exists
          if vim.fn.filereadable(lazyi18n_path) == 0 then
            vim.notify("lazyi18n not found at " .. lazyi18n_path, vim.log.levels.ERROR)
            return
          end
          
          -- Create floating terminal with lazyi18n
          local Terminal = require("toggleterm.terminal").Terminal
          local lazyi18n = Terminal:new({
            cmd = lazyi18n_path .. " " .. cwd,
            direction = "float",
            float_opts = {
              border = "curved",
              width = math.floor(vim.o.columns * 0.9),
              height = math.floor(vim.o.lines * 0.9),
            },
            on_open = function(term)
              vim.cmd("startinsert!")
            end,
          })
          lazyi18n:toggle()
        end,
        desc = "Open lazyi18n TUI",
      },
    },
  },
  
  -- Alternative: using snacks.nvim (if you have it)
  {
    "folke/snacks.nvim",
    optional = true,
    keys = {
      {
        "<leader>tI",
        function()
          local lazyi18n_path = vim.fn.expand("~/.local/share/lazyi18n/lazyi18n.sh")
          local cwd = vim.fn.getcwd()
          
          if vim.fn.filereadable(lazyi18n_path) == 0 then
            vim.notify("lazyi18n not found at " .. lazyi18n_path, vim.log.levels.ERROR)
            return
          end
          
          Snacks.terminal(lazyi18n_path .. " " .. cwd, {
            cwd = cwd,
            win = {
              position = "float",
              border = "rounded",
              width = 0.9,
              height = 0.9,
            },
          })
        end,
        desc = "Open lazyi18n (snacks)",
      },
    },
  },
}
