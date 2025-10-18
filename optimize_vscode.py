"""
VS Code Settings Optimizer for AI Stock Project
מייעל הגדרות VS Code עבור פרויקט AI Stock
"""

import json
import os
from pathlib import Path

def create_workspace_settings():
    """יוצר הגדרות workspace אופטימליות"""
    
    # VS Code workspace settings
    settings = {
        # Python settings
        "python.defaultInterpreterPath": "C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe",
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "basic",
        
        # Extensions to disable for this workspace
        "extensions.autoUpdate": False,
        
        # Performance settings
        "files.watcherExclude": {
            "**/.git/objects/**": True,
            "**/.git/subtree-cache/**": True,
            "**/node_modules/*/**": True,
            "**/__pycache__/**": True,
            "**/.env": False
        },
        
        # Azure settings
        "azure.tenant": "",
        "azure.cloud": "AzureCloud",
        
        # GitHub Copilot
        "github.copilot.enable": {
            "*": True,
            "yaml": False,
            "plaintext": False
        },
        
        # Terminal settings
        "terminal.integrated.defaultProfile.windows": "PowerShell",
        
        # File associations for AI/ML
        "files.associations": {
            "*.env": "dotenv",
            "*.ipynb": "jupyter-notebook"
        },
        
        # Recommended extensions (only essential ones)
        "extensions.recommendations": [
            "ms-python.python",
            "github.copilot",
            "ms-vscode.vscode-json",
            "ms-azuretools.vscode-azureresourcegroups",
            "ms-python.debugpy"
        ]
    }
    
    # Create .vscode directory if it doesn't exist
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    # Write settings
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created workspace settings: {settings_file}")
    return settings_file

def create_extensions_recommendations():
    """יוצר רשימת הרחבות מומלצות מינימלית"""
    
    extensions = {
        "recommendations": [
            # Core Python
            "ms-python.python",
            "ms-python.debugpy", 
            
            # AI & GitHub
            "github.copilot",
            "github.copilot-chat",
            
            # Azure (חיוני לפרויקט שלך)
            "ms-azuretools.vscode-azureresourcegroups",
            "ms-azuretools.vscode-azurefunctions",
            
            # Database
            "ms-mssql.mssql",
            
            # Essential utilities
            "ms-vscode.vscode-json",
            "ms-toolsai.jupyter"
        ],
        
        "unwantedRecommendations": [
            # Web development (לא נחוץ לפרויקט מניות)
            "ms-vscode.vscode-html",
            "ms-vscode.vscode-css",
            "ms-vscode.vscode-javascript",
            
            # Mobile development
            "ms-vscode.vscode-react-native",
            
            # Other languages
            "ms-vscode.cpptools",
            "ms-dotnettools.csharp",
            "oracle.oracle-developer-tools"
        ]
    }
    
    extensions_file = Path(".vscode/extensions.json")
    with open(extensions_file, 'w', encoding='utf-8') as f:
        json.dump(extensions, f, indent=2)
    
    print(f"✅ Created extensions config: {extensions_file}")
    return extensions_file

def main():
    """פונקציה ראשית"""
    print("🔧 VS Code Optimizer for AI Stock Project")
    print("=" * 50)
    
    try:
        # Create optimized settings
        settings_file = create_workspace_settings()
        extensions_file = create_extensions_recommendations()
        
        print("\n📋 הגדרות נוצרו בהצלחה:")
        print(f"  • {settings_file}")
        print(f"  • {extensions_file}")
        
        print("\n🎯 השלבים הבאים:")
        print("1. סגור את VS Code")
        print("2. פתח מחדש את הפרויקט")
        print("3. VS Code יציע להתקין/להסיר הרחבות")
        print("4. אשר ההתקנות והסרות המומלצות")
        print("5. הפעל מחדש VS Code")
        
        print("\n✅ זה אמור לפתור את בעיית ה-423 כלים!")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")

if __name__ == "__main__":
    main()