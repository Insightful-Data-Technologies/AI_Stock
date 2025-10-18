"""
Azure Static Web App Deployment with GoDaddy Domain
פריסת אתר Azure עם דומיין GoDaddy - aizevinstocks.com
"""

import json
import os
from datetime import datetime

def create_azure_deployment_with_godaddy():
    """יוצר תסריך פריסה שמתחשב בדומיין GoDaddy"""
    
    config = {
        "domain": "aizevinstocks.com",
        "project_name": "aizevinstocks",
        "resource_group": "aizevinstocks-rg", 
        "location": "East US 2",
        "github_repo": "https://github.com/Insightful-Data-Technologies/AI_Stock"
    }
    
    # Azure CLI commands for deployment
    azure_commands = f"""#!/bin/bash
# Azure Deployment for aizevinstocks.com
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 Deploying aizevinstocks.com to Azure"
echo "========================================"

# 1. Login and set subscription
echo "📋 Setting up Azure environment..."
az login
# az account set --subscription YOUR_SUBSCRIPTION_ID

# 2. Create Resource Group
echo "📁 Creating resource group..."
az group create \\
  --name {config['resource_group']} \\
  --location "{config['location']}"

# 3. Create Static Web App
echo "🌐 Creating Static Web App..."
az staticwebapp create \\
  --name {config['project_name']}-web \\
  --resource-group {config['resource_group']} \\
  --location "{config['location']}" \\
  --source {config['github_repo']} \\
  --branch main \\
  --app-location "/" \\
  --api-location "api" \\
  --output-location "website"

# 4. Get Static Web App details
echo "📊 Getting app details..."
STATIC_APP_URL=$(az staticwebapp show \\
  --name {config['project_name']}-web \\
  --resource-group {config['resource_group']} \\
  --query "defaultHostname" -o tsv)

echo "✅ Static Web App URL: https://$STATIC_APP_URL"

# 5. Add custom domain (GoDaddy)
echo "🔗 Adding custom domain: {config['domain']}"
az staticwebapp hostname set \\
  --name {config['project_name']}-web \\
  --resource-group {config['resource_group']} \\
  --hostname {config['domain']}

# 6. Get domain verification token
echo "🔐 Getting domain verification details..."
VERIFICATION_TOKEN=$(az staticwebapp hostname show \\
  --name {config['project_name']}-web \\
  --resource-group {config['resource_group']} \\
  --hostname {config['domain']} \\
  --query "validationToken" -o tsv)

echo "========================================"
echo "🎯 NEXT STEPS - UPDATE GODADDY DNS:"
echo "========================================"
echo "1. Go to GoDaddy DNS Management"
echo "2. Add these DNS records:"
echo ""
echo "   CNAME Record:"
echo "   Name: www"
echo "   Points to: $STATIC_APP_URL"
echo "   TTL: 1 Hour"
echo ""
echo "   CNAME Record (verification):"
echo "   Name: asuid"
echo "   Points to: $VERIFICATION_TOKEN"
echo "   TTL: 1 Hour"
echo ""
echo "   A Record (root domain):"
echo "   Name: @"
echo "   Points to: [Get IP from Azure Portal]"
echo "   TTL: 1 Hour"
echo ""
echo "3. Wait 5-60 minutes for DNS propagation"
echo "4. Check domain status in Azure Portal"
echo ""
echo "✅ Deployment completed!"
echo "🌐 Your site will be available at: https://{config['domain']}"
"""

    # Create the deployment script
    with open("deploy_with_godaddy.sh", "w", encoding="utf-8") as f:
        f.write(azure_commands)
    
    return azure_commands, config

def create_godaddy_dns_instructions():
    """יוצר הוראות מפורטות לעדכון DNS ב-GoDaddy"""
    
    instructions = {
        "step_by_step": {
            "1": {
                "title": "Access GoDaddy DNS Management",
                "actions": [
                    "Login to GoDaddy account",
                    "Go to 'My Products' → 'DNS'", 
                    "Select aizevinstocks.com",
                    "Click 'DNS Records'"
                ]
            },
            "2": {
                "title": "Delete existing records",
                "actions": [
                    "Delete the A record pointing to 160.153.0.150",
                    "Keep NS records as they are"
                ]
            },
            "3": {
                "title": "Add new DNS records",
                "records": [
                    {
                        "type": "CNAME",
                        "name": "www",
                        "points_to": "[Azure Static App URL].azurestaticapps.net",
                        "ttl": "1 Hour"
                    },
                    {
                        "type": "CNAME", 
                        "name": "asuid",
                        "points_to": "[Azure verification token]",
                        "ttl": "1 Hour"
                    },
                    {
                        "type": "A",
                        "name": "@", 
                        "points_to": "[Azure Static App IP]",
                        "ttl": "1 Hour"
                    }
                ]
            }
        },
        "verification": {
            "commands": [
                "nslookup aizevinstocks.com",
                "nslookup www.aizevinstocks.com", 
                "curl -I https://aizevinstocks.com"
            ]
        }
    }
    
    with open("godaddy_dns_instructions.json", "w", encoding="utf-8") as f:
        json.dump(instructions, f, indent=2, ensure_ascii=False)
    
    return instructions

def main():
    """פונקציה ראשית"""
    print("🌐 Azure + GoDaddy Deployment Setup")
    print("===================================")
    
    # Create deployment script
    azure_commands, config = create_azure_deployment_with_godaddy()
    print("✅ Created: deploy_with_godaddy.sh")
    
    # Create DNS instructions
    instructions = create_godaddy_dns_instructions()
    print("✅ Created: godaddy_dns_instructions.json")
    
    print(f"\n🎯 Ready to deploy {config['domain']}!")
    print("\n📋 Next steps:")
    print("1. Review deploy_with_godaddy.sh")
    print("2. Add your Azure subscription ID")
    print("3. Run: chmod +x deploy_with_godaddy.sh")
    print("4. Run: ./deploy_with_godaddy.sh")
    print("5. Update GoDaddy DNS as instructed")
    
    print(f"\n💰 Estimated cost: $50-200/month (from your $24k budget)")
    print(f"\n🌍 Domain: https://{config['domain']}")

if __name__ == "__main__":
    main()