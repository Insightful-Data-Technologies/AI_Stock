"""
Quick test of AI Agent with your Azure GPT-5 deployment
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables - override any existing ones
load_dotenv(override=True)

# Force correct endpoint from .env file
import os
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://chana-mfhwlu8b-eastus2.cognitiveservices.azure.com/'

async def test_azure_connection():
    """Test connection to your Azure GPT-5 deployment"""
    print("🧪 Testing AI Agent with your Azure GPT-5 deployment")
    print("=" * 60)
    
    try:
        from agents.ai_agent_client import AIAgentClient
        from config.ai_models_config import ai_models
        
        # Check configuration
        print("✅ AI modules imported successfully")
        
        # List available models
        models = ai_models.list_available_models()
        print(f"\n📋 Available models: {len(models)}")
        for key, name in models.items():
            print(f"  • {key}: {name}")
        
        # Test Azure GPT-5 connection
        print(f"\n🔧 Testing Azure GPT-5 deployment...")
        
        test_messages = [
            {"role": "system", "content": "You are a helpful AI assistant for stock analysis."},
            {"role": "user", "content": "Hello! Can you help me analyze stocks? Please respond briefly."}
        ]
        
        async with AIAgentClient() as client:
            print("🔗 Connecting to Azure GPT-5...")
            response = await client.chat_completion(
                messages=test_messages,
                model_key="azure_gpt5"
            )
            
            ai_response = response["choices"][0]["message"]["content"]
            print(f"✅ Azure GPT-5 Response: {ai_response[:100]}...")
            
        print("\n🎉 Connection successful! Your AI agent is ready!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Check your Azure credentials in .env file")
        return False

async def test_stock_analysis():
    """Test basic stock analysis"""
    print("\n📈 Testing Stock Analysis...")
    
    try:
        from agents.stock_ai_agent import analyze_stock
        
        sample_data = {
            "ticker": "AAPL",
            "current_price": 175.25,
            "pe_ratio": 28.5,
            "market_cap": 2800000000000
        }
        
        print("🔄 Running AI stock analysis...")
        result = await analyze_stock("AAPL", sample_data)
        
        print(f"✅ Analysis completed for {result.get('ticker', 'Unknown')}")
        
        if 'final_recommendation' in result:
            rec = result['final_recommendation'].get('recommendation', 'No recommendation')[:150]
            print(f"🎯 Recommendation: {rec}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Stock analysis error: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment setup...")
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_OPENAI_DEPLOYMENT",
        "DB_SERVER"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "key" in var.lower() or "password" in var.lower():
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            missing.append(var)
            print(f"  ❌ {var}: Not set")
    
    if missing:
        print(f"\n⚠️  Missing variables: {missing}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🚀 AI Stock Agent - Azure GPT-5 Integration Test")
    print("🤖 Testing your Azure deployment: gpt-5-chat-11")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup incomplete")
        print("💡 Please check your .env file")
        return
    
    # Test Azure connection
    if await test_azure_connection():
        # Test stock analysis
        await test_stock_analysis()
    
    print("\n" + "=" * 60)
    print("🎯 Next steps:")
    print("  1. If tests passed: You're ready to use the AI agent!")
    print("  2. If tests failed: Check Azure credentials and endpoint")
    print("  3. Try: from agents.stock_ai_agent import analyze_stock")
    print("  4. For database integration, run database connection tests")

if __name__ == "__main__":
    asyncio.run(main())