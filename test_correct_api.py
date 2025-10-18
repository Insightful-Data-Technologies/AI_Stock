import requests

# Using the actual API keys from your screenshot
api_key = "3mM44YwfE6i8uR_Uzbi3EzZPB9Sp8fTQK4cxr"
api_secret = "UfjZ1kQxPPsDHyecXbFsKY"

headers = {"Authorization": f"sso-key {api_key}:{api_secret}"}

print("🔍 Testing GoDaddy API connection...")
print(f"Key: {api_key[:10]}...")
print(f"Secret: {api_secret[:10]}...")
print()

# Test 1: Get specific domain info
print("📋 Test 1: Getting domain info for aizevinstocks.com")
try:
    r = requests.get("https://api.godaddy.com/v1/domains/aizevinstocks.com", headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("✅ Success!")
        print(r.json())
    else:
        print(f"❌ Error: {r.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

print()

# Test 2: List all domains
print("📋 Test 2: Listing all domains in account")
try:
    r2 = requests.get("https://api.godaddy.com/v1/domains", headers=headers, timeout=10)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        domains = r2.json()
        print(f"✅ Found {len(domains)} domains:")
        for domain in domains:
            print(f"  - {domain.get('domain', 'unknown')}")
    else:
        print(f"❌ Error: {r2.text}")
except Exception as e:
    print(f"❌ Exception: {e}")