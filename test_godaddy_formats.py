#!/usr/bin/env python3
"""
Simple GoDaddy API Test with different formats
"""

import requests
import os

# Test different API key formats
GODADDY_KEY = "3mM44YwfE6i8uR_Uzbi3EzZPB9Sp8fTQK4cxr"
GODADDY_SECRET = "UfjZ1kQxPPsDHyecXbFsKY"

def test_godaddy_connection():
    """Test GoDaddy API connection with different header formats"""
    
    # Test Format 1: sso-key format
    print("🔍 Testing Format 1: sso-key format")
    headers1 = {
        'Authorization': f'sso-key {GODADDY_KEY}:{GODADDY_SECRET}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.godaddy.com/v1/domains', headers=headers1, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print()
    
    # Test Format 2: Environment variable format
    print("🔍 Testing Format 2: Environment variables")
    os.environ['GODADDY_API_KEY'] = GODADDY_KEY
    os.environ['GODADDY_API_SECRET'] = GODADDY_SECRET
    
    headers2 = {
        'Authorization': f"sso-key {os.environ['GODADDY_API_KEY']}:{os.environ['GODADDY_API_SECRET']}",
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.godaddy.com/v1/domains', headers=headers2, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print()
    
    # Test Format 3: Basic auth style
    print("🔍 Testing Format 3: Different authorization format")
    headers3 = {
        'Authorization': f'{GODADDY_KEY}:{GODADDY_SECRET}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.godaddy.com/v1/domains', headers=headers3, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

    print()
    
    # Test the account info endpoint instead
    print("🔍 Testing Format 4: Account info endpoint")
    try:
        response = requests.get('https://api.godaddy.com/v1/shoppers/subaccount', headers=headers1, timeout=10)
        print(f"   Account info status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    print("🧪 GoDaddy API Connection Test")
    print("==============================")
    print(f"Using Key: {GODADDY_KEY[:10]}...")
    print(f"Using Secret: {GODADDY_SECRET[:10]}...")
    print()
    
    test_godaddy_connection()