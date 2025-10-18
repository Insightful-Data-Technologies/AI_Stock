# Manual DNS Configuration Guide

Since the GoDaddy API is not working yet, here's how to manually configure DNS:

## Current Status
✅ **Azure Static Web App Created**: `aizevinstocks-web`  
✅ **Default URL**: `victorious-smoke-01f2b7f0f.3.azurestaticapps.net`  
❌ **Custom Domain**: Not configured yet  
❌ **GoDaddy API**: Authentication failing  

## Next Steps

### Step 1: Purchase Domain (if not done)
1. Go to [GoDaddy.com](https://godaddy.com)
2. Search for "aizevinstocks.com"
3. Purchase the domain if available
4. Wait for domain to be active in your account

### Step 2: Manual DNS Configuration
Once you own the domain, configure these DNS records in GoDaddy:

**For root domain (aizevinstocks.com):**
```
Type: A
Name: @
Value: [Get from Azure Portal]
TTL: 3600
```

**For www subdomain:**
```
Type: CNAME
Name: www
Value: victorious-smoke-01f2b7f0f.3.azurestaticapps.net
TTL: 3600
```

**For domain verification:**
```
Type: TXT
Name: @
Value: [Get verification token from Azure]
TTL: 3600
```

### Step 3: Add Custom Domain in Azure
1. Go to Azure Portal
2. Navigate to your Static Web App: `aizevinstocks-web`
3. Go to "Custom domains" 
4. Click "Add custom domain"
5. Enter: `aizevinstocks.com`
6. Follow verification steps

### Step 4: Test Your Website
Your website will be available at:
- **Temporary**: https://victorious-smoke-01f2b7f0f.3.azurestaticapps.net
- **Final**: https://aizevinstocks.com (after DNS setup)

## Troubleshooting GoDaddy API
If API still fails:
- Wait 15-30 minutes for new API keys to activate
- Make sure domain is purchased and active
- Check if you need production vs sandbox environment