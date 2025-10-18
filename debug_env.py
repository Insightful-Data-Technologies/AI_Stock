"""Debug environment loading"""
import os
from dotenv import load_dotenv

print("🔍 Before loading .env:")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")

load_dotenv()

print("\n🔍 After loading .env:")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"AZURE_OPENAI_DEPLOYMENT: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")

# Also check the actual .env file content
print("\n📄 .env file content (first few lines):")
with open('.env', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[15:25], 16):
        if 'AZURE_OPENAI' in line:
            print(f"Line {i}: {line.strip()}")