import requests

# Your API credentials
api_key = "3mM44YwfE6i8uR_Uzbi3EzZPB9Sp8fTQK4cxr"
api_secret = "UfjZ1kQxPPsDHyecXbFsKY"

headers = {
    "Authorization": f"sso-key {api_key}:{api_secret}",
    "Content-Type": "application/json"
}

print("🔍 Testing GoDaddy API - Checking what domains you own...")
print()

# Try different endpoints to see what works
endpoints_to_test = [
    ("/v1/domains", "List all domains"),
    ("/v1/shoppers/subaccount", "Account info"),
    ("/v1/domains/available?domain=aizevinstocks.com", "Check if domain is available"),
]

for endpoint, description in endpoints_to_test:
    print(f"📋 {description}")
    try:
        url = f"https://api.godaddy.com{endpoint}"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            print(f"   ✅ Success: {result}")
        elif r.status_code == 401:
            print(f"   🔐 Authentication failed - API keys might be incorrect")
        elif r.status_code == 403:
            print(f"   🚫 Forbidden - might need different permissions")
        else:
            print(f"   ❌ Error: {r.text}")
            
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    print()

# Also check if the domain needs to be purchased
print("💡 If API fails, the domain might need to be purchased first!")
print("💡 You can buy 'aizevinstocks.com' directly from GoDaddy website")