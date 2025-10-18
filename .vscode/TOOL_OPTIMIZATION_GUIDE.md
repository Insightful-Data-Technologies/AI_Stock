# VS Code Tool Optimization Instructions

## How to reduce VS Code tools from 423 to minimal set:

### 1. Restart VS Code completely
- Close all windows
- Restart VS Code

### 2. Go to Configure Tools dialog:
- Press Ctrl+Shift+P
- Type "Configure Tools"
- Or click the gear icon in the bottom left

### 3. In the Configure Tools dialog:
- **UNCHECK "Built-in"** - This will disable most tools
- Keep only these checked:
  - ✅ edit (Edit files in your workspace)  
  - ✅ search (Search and read files)
  - ✅ runCommands (Run commands in terminal)
  - ✅ openSimpleBrowser (Preview websites)

### 4. Click "OK" to save

### Expected result:
- Tools should reduce from 423 to around 10-20
- VS Code will run much faster
- No performance degradation

### If tools increase again:
1. Check if new extensions were installed
2. Re-run this optimization process
3. Make sure .vscode/settings.json has the optimization settings

## Settings files created:
- `.vscode/settings.json` - Main optimization settings
- `.vscode/extensions.json` - Controls which extensions to install/avoid

## Performance improvements:
- Faster startup
- Less memory usage  
- Reduced tool suggestions
- Better focus on essential tools only