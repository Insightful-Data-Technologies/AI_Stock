#!/bin/bash
# Azure Website Deployment Script
# AI Stock Analysis Platform
# Generated: 2025-10-18 17:21:59

echo "🚀 Starting Azure deployment for AI Stock Analysis Platform"
echo "=================================================="

echo "📋 SETUP"
echo "--------------------------------------------------"
# 1. Login to Azure
az login

# 2. Set default subscription
az account set --subscription 

# 3. Create Resource Group
az group create --name ai-stock-analysis-rg --location 'East US 2'


echo "📋 STATIC WEB APP"
echo "--------------------------------------------------"
# 4. Create Static Web App
az staticwebapp create \
  --name ai-stock-analysis-web \
  --resource-group ai-stock-analysis-rg \
  --location 'East US 2' \
  --source https://github.com/Insightful-Data-Technologies/AI_Stock \
  --branch main \
  --app-location '/' \
  --api-location 'api' \
  --output-location 'dist'


echo "📋 FUNCTION APP"
echo "--------------------------------------------------"
# 5. Create Storage Account for Functions
az storage account create \
  --name aistockanalysisstorage \
  --resource-group ai-stock-analysis-rg \
  --location 'East US 2' \
  --sku Standard_LRS

# 6. Create Function App
az functionapp create \
  --name ai-stock-analysis-functions \
  --resource-group ai-stock-analysis-rg \
  --storage-account aistockanalysisstorage \
  --consumption-plan-location 'East US 2' \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4


echo "📋 DATABASE"
echo "--------------------------------------------------"
# 7. Create Azure SQL Database (Optional - or use existing)
az sql server create \
  --name ai-stock-analysis-sql-server \
  --resource-group ai-stock-analysis-rg \
  --location 'East US 2' \
  --admin-user aistock-admin \
  --admin-password 'ComplexPassword123!'

az sql db create \
  --resource-group ai-stock-analysis-rg \
  --server ai-stock-analysis-sql-server \
  --name AI_Stocks_Web \
  --service-objective S1


echo "📋 KEY VAULT"
echo "--------------------------------------------------"
# 8. Create Key Vault for secrets
az keyvault create \
  --name ai-stock-analysis-kv \
  --resource-group ai-stock-analysis-rg \
  --location 'East US 2'

# 9. Add secrets to Key Vault
az keyvault secret set --vault-name ai-stock-analysis-kv --name 'azure-openai-key' --value 'your-azure-openai-key'
az keyvault secret set --vault-name ai-stock-analysis-kv --name 'database-connection' --value 'your-db-connection-string'


echo "📋 MONITORING"
echo "--------------------------------------------------"
# 10. Create Application Insights
az monitor app-insights component create \
  --app ai-stock-analysis-insights \
  --location 'East US 2' \
  --resource-group ai-stock-analysis-rg \
  --kind web


echo "✅ Deployment completed!"
echo "🌐 Check your resources in Azure Portal"
echo "📊 Next steps: Configure Power BI and upload website content"
