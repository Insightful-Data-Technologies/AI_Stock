"""
GoDaddy DNS Automation for Azure Static Web App
Automation for updating DNS in GoDaddy for Azure site
"""

import requests
import json
import time
import os
from typing import Dict, List

class GoDaddyDNSManager:
    """DNS Manager for GoDaddy"""
    
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
        self.base_url = "https://api.godaddy.com/v1"
        self.headers = {
            "Authorization": f"sso-key {api_key}:{secret}",
            "Content-Type": "application/json"
        }
    
    def get_domain_records(self, domain: str) -> List[Dict]:
        """Get current DNS records"""
        url = f"{self.base_url}/domains/{domain}/records"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting DNS records: {e}")
            return []
    
    def update_dns_record(self, domain: str, record_type: str, name: str, data: str, ttl: int = 3600) -> bool:
        """Update DNS record"""
        url = f"{self.base_url}/domains/{domain}/records/{record_type}/{name}"
        
        record_data = [{
            "data": data,
            "ttl": ttl
        }]
        
        try:
            response = requests.put(url, headers=self.headers, json=record_data)
            response.raise_for_status()
            print(f"✅ {record_type} record ({name}) updated successfully: {data}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating {record_type} record ({name}): {e}")
            return False
    
    def add_dns_record(self, domain: str, records: List[Dict]) -> bool:
        """Add new DNS records"""
        url = f"{self.base_url}/domains/{domain}/records"
        
        try:
            response = requests.patch(url, headers=self.headers, json=records)
            response.raise_for_status()
            print("✅ DNS records added successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error adding DNS records: {e}")
            return False
    
    def setup_azure_static_app_dns(self, domain: str, azure_app_url: str, verification_token: str) -> bool:
        """Setup DNS for Azure Static Web App"""
        
        print(f"🔧 Setting up DNS for {domain} → {azure_app_url}")
        
        # Required DNS records
        dns_records = [
            {
                "type": "CNAME",
                "name": "www",
                "data": azure_app_url,
                "ttl": 3600
            },
            {
                "type": "TXT", 
                "name": "@",
                "data": f"ms-domain-verification={verification_token}",
                "ttl": 3600
            }
        ]
        
        success = True
        
        # Update records one by one
        for record in dns_records:
            if record["type"] == "CNAME":
                success &= self.update_dns_record(
                    domain, record["type"], record["name"], 
                    record["data"], record["ttl"]
                )
            else:  # TXT record
                success &= self.add_dns_record(domain, [record])
        
        if success:
            print("✅ כל רשומות ה-DNS עודכנו בהצלחה!")
            print("⏰ יידרש זמן propagation של 5-60 דקות")
        
        return success

def get_azure_static_app_info(resource_group: str, app_name: str) -> Dict:
    """קבלת מידע על Azure Static Web App"""
    
    print("📊 מקבל מידע על Azure Static Web App...")
    
    # Get app URL
    import subprocess
    
    try:
        # קבלת URL של האפליקציה
        result = subprocess.run([
            "az", "staticwebapp", "show",
            "--name", app_name,
            "--resource-group", resource_group,
            "--query", "defaultHostname",
            "-o", "tsv"
        ], capture_output=True, text=True, check=True)
        
        app_url = result.stdout.strip()
        
        print(f"✅ Azure Static Web App URL: {app_url}")
        
        return {
            "app_url": app_url,
            "verification_token": "placeholder-token"  # נקבל אותו מאחר
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ שגיאה בקבלת מידע Azure: {e}")
        return {}

def main():
    """פונקציה ראשית"""
    
    # Configuration
    GODADDY_API_KEY = "3mM44YwfE6i8uR_Uzbi3EzZPB9Sp8fTQK4cxr"
    GODADDY_SECRET = "UfjZ1kQxPPsDHyecXbFsKY"
    DOMAIN = "aizevinstocks.com"
    AZURE_RG = "rg-aizevinstocks"
    AZURE_APP = "aizevinstocks-web"
    
    print("🌐 GoDaddy DNS Automation for Azure")
    print("===================================")
    
    # Create DNS manager
    dns_manager = GoDaddyDNSManager(GODADDY_API_KEY, GODADDY_SECRET)
    
    # Check current records
    print(f"🔍 Checking current DNS records for {DOMAIN}...")
    current_records = dns_manager.get_domain_records(DOMAIN)
    
    if current_records:
        print("📋 Current DNS records:")
        for record in current_records[:5]:  # Show first 5
            print(f"  {record.get('type')} | {record.get('name')} | {record.get('data')}")
    
    # Get Azure info
    azure_info = get_azure_static_app_info(AZURE_RG, AZURE_APP)
    
    if not azure_info:
        print("❌ Unable to get Azure info. Please try again.")
        return
    
    # Setup DNS
    success = dns_manager.setup_azure_static_app_dns(
        DOMAIN, 
        azure_info["app_url"],
        "verification-token-placeholder"
    )
    
    if success:
        print("\n🎉 DNS configured successfully!")
        print(f"🌍 Website will be available at: https://{DOMAIN}")
        print("⏰ Wait 5-60 minutes for DNS propagation")
        
        # Next steps instructions
        print("\n📋 Next steps:")
        print("1. Go back to Azure Portal")
        print("2. Add Custom Domain in the application")
        print("3. Perform Domain Verification")
        print("4. Enable SSL Certificate")
        
    else:
        print("❌ There was an error setting up DNS")

if __name__ == "__main__":
    main()