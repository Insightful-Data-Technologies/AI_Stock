# 🌐 GoDaddy Domain Configuration for Azure Static Web App
# הגדרת דומיין GoDaddy לאתר Azure

## Current Status ✅
- **Domain:** aizevinstocks.com
- **Registrar:** GoDaddy
- **Current DNS:** GoDaddy default nameservers

## 🎯 Connection Process: GoDaddy → Azure

### Step 1: Azure Static Web App Setup
1. **Create Azure Static Web App first**
2. **Get the default Azure URL** (will be something like: `happy-tree-abc123.azurestaticapps.net`)
3. **Get Custom Domain verification token**

### Step 2: GoDaddy DNS Configuration

#### Required DNS Records in GoDaddy:

**A. CNAME Record for www:**
```
Type: CNAME
Name: www
Value: [your-azure-static-app].azurestaticapps.net
TTL: 1 Hour
```

**B. CNAME Record for domain verification:**
```
Type: CNAME  
Name: asuid.aizevinstocks.com
Value: [Azure-provided-verification-token]
TTL: 1 Hour
```

**C. A Record for root domain:**
```
Type: A
Name: @
Value: [Azure Static Web App IP]
TTL: 1 Hour
```

### Step 3: Azure Custom Domain Configuration

1. **In Azure Portal:**
   - Go to your Static Web App
   - Navigate to "Custom domains"
   - Click "Add custom domain"
   - Enter: `aizevinstocks.com`
   - Select domain type: "Other"

2. **Domain Verification:**
   - Azure will provide a verification token
   - Add this as CNAME in GoDaddy (step 2B above)
   - Wait for verification (5-10 minutes)

3. **SSL Certificate:**
   - Azure will automatically generate SSL certificate
   - This may take 5-15 minutes
   - Certificate will auto-renew

### Step 4: Update GoDaddy DNS Records

Based on what I see in your GoDaddy panel, you'll need to:

1. **Replace the A record (160.153.0.150)** with Azure's IP
2. **Update NS records** to point to Azure's nameservers (optional)
3. **Add CNAME for www subdomain**

## 🔧 Detailed Configuration Steps

### In GoDaddy DNS Management:

1. **Delete existing A record (160.153.0.150)**
2. **Add new records:**

```dns
# Root domain A record
Type: A
Name: @
Points to: [Will get from Azure]
TTL: 1 Hour

# WWW subdomain  
Type: CNAME
Name: www
Points to: [your-app].azurestaticapps.net
TTL: 1 Hour

# Domain verification
Type: CNAME
Name: asuid
Points to: [Azure verification token]
TTL: 1 Hour
```

### In Azure Portal:

1. **Create Static Web App with custom domain**
2. **Get the required values:**
   - Azure Static App URL
   - Verification token
   - IP address (if using A record)

## 📋 Azure CLI Commands for Domain Setup

```bash
# Create Static Web App with custom domain
az staticwebapp create \
  --name aizevinstocks-web \
  --resource-group ai-stock-analysis-rg \
  --location "East US 2" \
  --source https://github.com/Insightful-Data-Technologies/AI_Stock \
  --branch main \
  --app-location '/' \
  --api-location 'api' \
  --output-location 'dist'

# Add custom domain
az staticwebapp hostname set \
  --name aizevinstocks-web \
  --resource-group ai-stock-analysis-rg \
  --hostname aizevinstocks.com

# Verify domain ownership
az staticwebapp hostname show \
  --name aizevinstocks-web \
  --resource-group ai-stock-analysis-rg \
  --hostname aizevinstocks.com
```

## 🚀 Quick Action Plan

**What we need to do now:**

1. **First:** Create the Azure Static Web App
2. **Then:** Get the Azure-provided values
3. **Finally:** Update GoDaddy DNS with the correct records

Would you like me to:
- Create the Azure deployment script with domain configuration?
- Prepare the exact DNS records you'll need to add in GoDaddy?
- Set up the Static Web App now?

## 💡 Pro Tips:

- **Propagation time:** DNS changes take 5-60 minutes
- **SSL generation:** Takes 5-15 minutes after domain verification  
- **Testing:** Use `nslookup aizevinstocks.com` to verify DNS
- **Monitoring:** Azure provides domain status in the portal

Ready to start the deployment? 🎯