"""
Simple Azure GPT-5 Stock Analysis Test
Uses only your working Azure deployment
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables - override any existing ones
load_dotenv(override=True)

# Force correct endpoint from .env file
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://chana-mfhwlu8b-eastus2.cognitiveservices.azure.com/'

async def test_simple_analysis():
    """Test simple stock analysis with Azure GPT-5 only"""
    print("🚀 Testing Azure GPT-5 Stock Analysis")
    print("=" * 50)
    
    try:
        from agents.ai_agent_client import AIAgentClient
        
        # Test messages for stock analysis
        messages = [
            {"role": "system", "content": """You are an expert financial analyst. Provide concise stock analysis based on available knowledge."""},
            {"role": "user", "content": """Analyze Apple (AAPL) stock briefly:
1. Current company performance
2. Key strengths 
3. Main risks
4. Investment outlook
Keep response under 200 words."""}
        ]
        
        print("🔍 Analyzing Apple (AAPL) with Azure GPT-5...")
        
        async with AIAgentClient() as client:
            response = await client.chat_completion(
                messages=messages,
                model_key="azure_gpt5"  # Use only your working Azure GPT-5
            )
            
            if response and 'choices' in response:
                analysis = response['choices'][0]['message']['content']
                print("\n📊 GPT-5 Stock Analysis:")
                print("=" * 50)
                print(analysis)
                print("=" * 50)
                print("✅ Azure GPT-5 analysis completed successfully!")
                return True
            else:
                print("❌ Unexpected response format")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main test function"""
    print("🎯 Azure GPT-5 Stock Analysis Test")
    
    # Test simple analysis
    success = await test_simple_analysis()
    
    if success:
        print("\n🎉 SUCCESS: Your Azure GPT-5 is working perfectly for stock analysis!")
        print("\n💡 Next steps:")
        print("  • You can now use the AI agent for stock analysis")
        print("  • Consider setting up GitHub token for additional models")
        print("  • Test database connection for full functionality")
    else:
        print("\n❌ Tests failed - check configuration")

if __name__ == "__main__":
    asyncio.run(main())