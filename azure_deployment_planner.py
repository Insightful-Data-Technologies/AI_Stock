"""
Azure Website Deployment Script for AI Stock Analysis
תסריך פריסת אתר ניתוח מניות AI באזור
"""

import json
import os
from datetime import datetime

class AzureWebsiteDeployment:
    """מחלקה לניהול פריסת אתר באזור"""
    
    def __init__(self):
        self.project_name = "ai-stock-analysis"
        self.resource_group = f"{self.project_name}-rg"
        self.location = "East US 2"  # זה המיקום של ה-Azure OpenAI שלך
        self.subscription_id = ""  # נצטרך להשלים
        self.domain_name = "aizevinstocks.com"
        
    def generate_azure_cli_commands(self):
        """יוצר פקודות Azure CLI לפריסה"""
        
        commands = {
            "setup": [
                "# 1. Login to Azure",
                "az login",
                "",
                "# 2. Set default subscription", 
                f"az account set --subscription {self.subscription_id}",
                "",
                "# 3. Create Resource Group",
                f"az group create --name {self.resource_group} --location '{self.location}'",
                ""
            ],
            
            "static_web_app": [
                "# 4. Create Static Web App",
                f"az staticwebapp create \\",
                f"  --name {self.project_name}-web \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --location '{self.location}' \\",
                f"  --source https://github.com/Insightful-Data-Technologies/AI_Stock \\",
                f"  --branch main \\",
                f"  --app-location '/' \\",
                f"  --api-location 'api' \\",
                f"  --output-location 'dist'",
                ""
            ],
            
            "function_app": [
                "# 5. Create Storage Account for Functions",
                f"az storage account create \\",
                f"  --name {self.project_name.replace('-', '')}storage \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --location '{self.location}' \\",
                f"  --sku Standard_LRS",
                "",
                "# 6. Create Function App",
                f"az functionapp create \\",
                f"  --name {self.project_name}-functions \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --storage-account {self.project_name.replace('-', '')}storage \\",
                f"  --consumption-plan-location '{self.location}' \\",
                f"  --runtime python \\",
                f"  --runtime-version 3.11 \\",
                f"  --functions-version 4",
                ""
            ],
            
            "database": [
                "# 7. Create Azure SQL Database (Optional - or use existing)",
                f"az sql server create \\",
                f"  --name {self.project_name}-sql-server \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --location '{self.location}' \\",
                f"  --admin-user aistock-admin \\",
                f"  --admin-password 'ComplexPassword123!'",
                "",
                f"az sql db create \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --server {self.project_name}-sql-server \\",
                f"  --name AI_Stocks_Web \\",
                f"  --service-objective S1",
                ""
            ],
            
            "key_vault": [
                "# 8. Create Key Vault for secrets",
                f"az keyvault create \\",
                f"  --name {self.project_name}-kv \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --location '{self.location}'",
                "",
                "# 9. Add secrets to Key Vault",
                "az keyvault secret set --vault-name ai-stock-analysis-kv --name 'azure-openai-key' --value 'your-azure-openai-key'",
                "az keyvault secret set --vault-name ai-stock-analysis-kv --name 'database-connection' --value 'your-db-connection-string'",
                ""
            ],
            
            "monitoring": [
                "# 10. Create Application Insights",
                f"az monitor app-insights component create \\",
                f"  --app {self.project_name}-insights \\",
                f"  --location '{self.location}' \\",
                f"  --resource-group {self.resource_group} \\",
                f"  --kind web",
                ""
            ]
        }
        
        return commands
    
    def create_deployment_script(self):
        """יוצר תסריך פריסה מלא"""
        
        commands = self.generate_azure_cli_commands()
        
        script_content = f"""#!/bin/bash
# Azure Website Deployment Script
# AI Stock Analysis Platform
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 Starting Azure deployment for AI Stock Analysis Platform"
echo "=================================================="

"""
        
        for section, section_commands in commands.items():
            script_content += f"echo \"📋 {section.upper().replace('_', ' ')}\"\n"
            script_content += "echo \"--------------------------------------------------\"\n"
            for command in section_commands:
                script_content += f"{command}\n"
            script_content += "\n"
        
        script_content += """echo "✅ Deployment completed!"
echo "🌐 Check your resources in Azure Portal"
echo "📊 Next steps: Configure Power BI and upload website content"
"""
        
        return script_content
    
    def create_website_structure(self):
        """יוצר מבנה קבצים לאתר"""
        
        structure = {
            "src": {
                "pages": [
                    "Home.vue",
                    "Performance.vue", 
                    "RiskManagement.vue",
                    "Technology.vue",
                    "About.vue"
                ],
                "components": [
                    "Navigation.vue",
                    "Footer.vue",
                    "Charts/PerformanceChart.vue",
                    "Charts/RiskChart.vue",
                    "Dashboard/LiveDashboard.vue"
                ],
                "assets": [
                    "styles/main.css",
                    "images/logo.png",
                    "data/sample-data.json"
                ]
            },
            "api": {
                "functions": [
                    "GetStockData/__init__.py",
                    "GetPerformanceMetrics/__init__.py", 
                    "GetRiskAnalysis/__init__.py",
                    "requirements.txt"
                ]
            },
            "public": [
                "index.html",
                "favicon.ico"
            ],
            "config": [
                "package.json",
                "vue.config.js",
                "azure-pipelines.yml"
            ]
        }
        
        return structure

def main():
    """פונקציה ראשית"""
    
    print("🌟 Azure Website Deployment Planner")
    print("===================================")
    
    deployment = AzureWebsiteDeployment()
    
    # Create deployment script
    script_content = deployment.create_deployment_script()
    
    with open("deploy_azure_website.sh", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ Created: deploy_azure_website.sh")
    
    # Create website structure plan
    structure = deployment.create_website_structure()
    
    with open("website_structure.json", "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print("✅ Created: website_structure.json")
    
    print("\n🎯 Next Steps:")
    print("1. Review deploy_azure_website.sh")
    print("2. Add your Azure subscription ID")
    print("3. Run: chmod +x deploy_azure_website.sh")
    print("4. Run: ./deploy_azure_website.sh")
    print("\n💰 Estimated monthly cost: $200-500 (well within your $24k budget!)")

if __name__ == "__main__":
    main()