#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GoDaddy API Connection Test
"""

import requests

# API Configuration - values from the new screenshot
GODADDY_KEY = "3mM44YwfE6i8uR_Uzbi3EzZPB9Sp8fTQK4cxr"
GODADDY_SECRET = "UfjZ1kQxPPsDHyecXbFsKY"

headers = {
    'Authorization': f'sso-key {GODADDY_KEY}:{GODADDY_SECRET}',
    'Content-Type': 'application/json'
}

try:
    print("🔍 Testing GoDaddy API connection...")
    print(f"🔐 Using API Key: {GODADDY_KEY[:10]}...")
    response = requests.get('https://api.godaddy.com/v1/domains', headers=headers)
    
    print(f"📊 Response code: {response.status_code}")
    
    if response.status_code == 200:
        domains = response.json()
        print(f"✅ Found {len(domains)} domains:")
        for domain in domains:
            domain_name = domain.get('domain', 'unknown')
            domain_status = domain.get('status', 'unknown')
            print(f"   - {domain_name} (status: {domain_status})")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"📄 Error content: {response.text}")

except Exception as e:
    print(f"❌ Connection error: {e}")