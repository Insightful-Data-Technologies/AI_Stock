# 📋 GoDaddy DNS Records Update Checklist
# רשימת בדיקה לעדכון רשומות DNS ב-GoDaddy

## 🎯 Quick Action Items

### Before Starting:
1. ✅ Run Azure deployment: `./deploy_with_godaddy.sh`
2. ✅ Copy the Azure values from the output
3. ✅ Login to GoDaddy with username: chananz

### GoDaddy Login:
- **URL:** https://dcc.godaddy.com/control/dnsmanagement?domainName=aizevinstocks.com
- **Username:** chananz
- **Password:** [your password]

### Current DNS Records to Delete:
```
❌ DELETE: A Record @ → 160.153.0.150
✅ KEEP: NS Records (ns41.domaincontrol.com, ns42.domaincontrol.com)
```

### New DNS Records to Add:
```
🔹 CNAME | www | [from Azure].azurestaticapps.net | 1 Hour
🔹 CNAME | asuid | [from Azure verification] | 1 Hour  
🔹 A | @ | [from Azure IP] | 1 Hour
```

## 📝 Values You'll Get from Azure Deployment:

After running the deployment script, look for these in the output:

1. **Static Web App URL:**
   ```
   ✅ Static Web App URL: https://[APP-NAME].azurestaticapps.net
   ```
   → Use `[APP-NAME].azurestaticapps.net` for the www CNAME

2. **Verification Token:**
   ```
   🔐 Verification Token: [TOKEN].azurestaticapps.net
   ```
   → Use this for the asuid CNAME

3. **IP Address:**
   ```
   📍 IP Address: [IP-ADDRESS]
   ```
   → Use this for the @ A record

## ⚡ Quick Copy-Paste Template:

**For www CNAME:**
- Type: CNAME
- Name: www
- Points to: `PASTE_AZURE_URL_HERE.azurestaticapps.net`
- TTL: 1 Hour

**For verification CNAME:**
- Type: CNAME
- Name: asuid
- Points to: `PASTE_VERIFICATION_TOKEN_HERE`
- TTL: 1 Hour

**For root A record:**
- Type: A
- Name: @
- Points to: `PASTE_IP_ADDRESS_HERE`
- TTL: 1 Hour

## 🕐 Timeline Expectations:

- Azure deployment: 5-10 minutes
- DNS update in GoDaddy: 2 minutes
- DNS propagation: 15-60 minutes
- SSL certificate: 10-20 minutes
- **Total:** ~30-90 minutes until live

## ✅ Success Check:

1. Visit: https://aizevinstocks.com
2. Should show your AI Stock Analysis website
3. Green SSL lock in browser
4. All sections work correctly

## 🆘 If Something Goes Wrong:

1. **Double-check the DNS values** in GoDaddy match Azure output exactly
2. **Wait longer** - DNS can take up to 24 hours (usually much faster)
3. **Clear browser cache** and try incognito mode
4. **Check from different device/network**

---

**Ready? Let's deploy your website! 🚀**