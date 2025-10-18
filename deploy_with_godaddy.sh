#!/bin/bash
# Azure Deployment for aizevinstocks.com
# Generated: 2025-10-18 17:27:23

echo "🚀 Deploying aizevinstocks.com to Azure"
echo "========================================"

# 1. Login and set subscription
echo "📋 Setting up Azure environment..."
az login
# az account set --subscription YOUR_SUBSCRIPTION_ID

# 2. Create Resource Group
echo "📁 Creating resource group..."
az group create \
  --name aizevinstocks-rg \
  --location "East US 2"

# 3. Create Static Web App
echo "🌐 Creating Static Web App..."
az staticwebapp create \
  --name aizevinstocks-web \
  --resource-group aizevinstocks-rg \
  --location "East US 2" \
  --source https://github.com/Insightful-Data-Technologies/AI_Stock \
  --branch main \
  --app-location "/" \
  --api-location "api" \
  --output-location "website"

# 4. Get Static Web App details
echo "📊 Getting app details..."
STATIC_APP_URL=$(az staticwebapp show \
  --name aizevinstocks-web \
  --resource-group aizevinstocks-rg \
  --query "defaultHostname" -o tsv)

echo "✅ Static Web App URL: https://$STATIC_APP_URL"

# 5. Add custom domain (GoDaddy)
echo "🔗 Adding custom domain: aizevinstocks.com"
az staticwebapp hostname set \
  --name aizevinstocks-web \
  --resource-group aizevinstocks-rg \
  --hostname aizevinstocks.com

# 6. Get domain verification token
echo "🔐 Getting domain verification details..."
VERIFICATION_TOKEN=$(az staticwebapp hostname show \
  --name aizevinstocks-web \
  --resource-group aizevinstocks-rg \
  --hostname aizevinstocks.com \
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
echo "🌐 Your site will be available at: https://aizevinstocks.com"
