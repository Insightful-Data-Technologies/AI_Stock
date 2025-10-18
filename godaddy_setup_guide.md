# 🌐 GoDaddy DNS Setup Guide for aizevinstocks.com
# מדריך הגדרת DNS ב-GoDaddy עבור aizevinstocks.com

## 🔐 Account Details
**Username:** chananz
**Domain:** aizevinstocks.com
**Target:** Azure Static Web App

## 📋 Step-by-Step Instructions

### Phase 1: Access GoDaddy DNS Management

1. **Login to GoDaddy:**
   - Go to: https://dcc.godaddy.com/control/dnsmanagement?domainName=aizevinstocks.com
   - Username: chananz
   - Password: [your password]

2. **Navigate to DNS Management:**
   - Click "My Products"
   - Select "DNS" 
   - Click on "aizevinstocks.com"
   - Click "DNS Records"

### Phase 2: Clean Current DNS Records

**Current records to modify/delete:**

1. **Delete existing A record:**
   - Type: A
   - Name: @
   - Points to: 160.153.0.150
   - **Action: DELETE this record**

2. **Keep existing NS records:**
   - Type: NS 
   - Name: (blank)
   - Points to: ns41.domaincontrol.com, ns42.domaincontrol.com
   - **Action: KEEP these as they are**

### Phase 3: Add New Azure DNS Records

**After running the Azure deployment, you'll get these values:**

#### Record 1: WWW Subdomain
```
Type: CNAME
Name: www
Points to: [AZURE_STATIC_APP_URL].azurestaticapps.net
TTL: 1 Hour
```

#### Record 2: Domain Verification
```
Type: CNAME
Name: asuid
Points to: [AZURE_VERIFICATION_TOKEN]
TTL: 1 Hour
```

#### Record 3: Root Domain
```
Type: A
Name: @
Points to: [AZURE_STATIC_APP_IP]
TTL: 1 Hour
```

## 🚀 Deployment Process

### Step 1: Run Azure Deployment First

```bash
# 1. Navigate to your project
cd C:\AI_Stock

# 2. Run the deployment script
./deploy_with_godaddy.sh
```

**This will give you the values you need for GoDaddy DNS.**

### Step 2: Get Azure Values

After running the deployment, you'll see output like:
```
✅ Static Web App URL: https://happy-tree-abc123.azurestaticapps.net
🔐 Verification Token: abc123def456.azurestaticapps.net
📍 IP Address: 20.50.4.25
```

### Step 3: Update GoDaddy DNS

1. **Go back to GoDaddy DNS Management**
2. **Delete the old A record (160.153.0.150)**
3. **Add the three new records using the values from Azure**

### Step 4: Wait and Verify

- **DNS Propagation:** 5-60 minutes
- **SSL Certificate:** 5-15 minutes after DNS propagation
- **Test:** Visit https://aizevinstocks.com

## 🧪 Verification Commands

Run these to check if DNS is working:

```bash
# Check root domain
nslookup aizevinstocks.com

# Check www subdomain  
nslookup www.aizevinstocks.com

# Check if website is live
curl -I https://aizevinstocks.com
```

## 📊 Expected Timeline

- **Azure deployment:** 5-10 minutes
- **DNS update in GoDaddy:** 2-5 minutes
- **DNS propagation:** 5-60 minutes
- **SSL certificate generation:** 5-15 minutes
- **Total time:** 20-90 minutes

## 🔍 Troubleshooting

### If DNS doesn't propagate:
1. Double-check the record values in GoDaddy
2. Wait up to 24 hours (usually much faster)
3. Clear your browser cache
4. Try accessing from a different device/network

### If SSL certificate fails:
1. Verify domain ownership in Azure Portal
2. Check that the verification CNAME is correct
3. Wait additional 15 minutes

## 📞 Support Contacts

- **GoDaddy Support:** If you have issues accessing DNS management
- **Azure Support:** If deployment fails
- **Domain Status Check:** https://www.whatsmydns.net/#CNAME/www.aizevinstocks.com

## ✅ Success Criteria

You'll know everything is working when:
1. ✅ https://aizevinstocks.com loads your website
2. ✅ https://www.aizevinstocks.com redirects properly  
3. ✅ SSL certificate shows as valid (green lock in browser)
4. ✅ All sections of your website work correctly

---

**Ready to start? Run the Azure deployment first, then follow this guide to update GoDaddy!** 🚀