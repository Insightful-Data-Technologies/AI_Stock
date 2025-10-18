"""
Demo: AI Stock Analysis Agent
Shows how to use GPT-5 and Azure AI Foundry for stock analysis
"""
import asyncio
import os
from datetime import datetime
import json

# Set up environment variables (you'll need to create a .env file)
from dotenv import load_dotenv
load_dotenv()

from agents.stock_ai_agent import StockAIAgent, analyze_stock

async def demo_stock_analysis():
    """Demo comprehensive stock analysis"""
    
    print("🤖 AI Stock Analysis Agent Demo")
    print("=" * 50)
    
    # Sample stock data (in real implementation, this would come from your database)
    sample_stock_data = {
        "ticker": "AAPL",
        "current_price": 175.25,
        "price_history": [170, 172, 174, 175, 173, 175.25],
        "volume": 45000000,
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "dividend_yield": 0.44,
        "52_week_high": 180.50,
        "52_week_low": 155.30,
        "news_sentiment": "positive",
        "analyst_ratings": {"buy": 15, "hold": 8, "sell": 2}
    }
    
    try:
        # Method 1: Using the utility function
        print("\n📊 Running comprehensive analysis...")
        result = await analyze_stock("AAPL", sample_stock_data)
        
        print(f"\n✅ Analysis completed for {result['ticker']}")
        print(f"📅 Timestamp: {result['timestamp']}")
        
        # Display results
        for analysis_type in ['technical_analysis', 'fundamental_analysis', 'sentiment_analysis', 'risk_assessment']:
            if analysis_type in result:
                print(f"\n📈 {analysis_type.replace('_', ' ').title()}:")
                if 'key_points' in result[analysis_type]:
                    for point in result[analysis_type]['key_points'][:3]:  # Show top 3
                        print(f"  • {point}")
        
        # Show final recommendation
        if 'final_recommendation' in result:
            print(f"\n🎯 Final Recommendation:")
            rec_content = result['final_recommendation']['recommendation'][:200]  # First 200 chars
            print(f"  {rec_content}...")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("💡 Make sure you have set up your API keys in .env file")

async def demo_strategy_generation():
    """Demo AI trading strategy generation"""
    
    print("\n\n🧠 AI Strategy Generation Demo")
    print("=" * 50)
    
    try:
        async with StockAIAgent() as agent:
            strategy = await agent.generate_trading_strategy(
                strategy_requirements="Create a momentum-based trading strategy for tech stocks",
                risk_tolerance="moderate",
                timeframe="medium_term"
            )
            
            print("✅ Trading strategy generated successfully!")
            print(f"📅 Generated at: {strategy['generated_at']}")
            print(f"🎯 Risk tolerance: {strategy['risk_tolerance']}")
            print(f"⏰ Timeframe: {strategy['timeframe']}")
            
            # Show a snippet of the strategy
            strategy_snippet = strategy['strategy_code'][:300]
            print(f"\n📝 Strategy Code Snippet:")
            print(f"```python\n{strategy_snippet}...\n```")
            
    except Exception as e:
        print(f"❌ Error generating strategy: {e}")

async def demo_portfolio_optimization():
    """Demo AI portfolio optimization"""
    
    print("\n\n💼 AI Portfolio Optimization Demo") 
    print("=" * 50)
    
    sample_portfolio = {
        "holdings": {
            "AAPL": {"shares": 100, "current_price": 175.25},
            "MSFT": {"shares": 50, "current_price": 380.50},
            "GOOGL": {"shares": 25, "current_price": 140.75},
            "TSLA": {"shares": 30, "current_price": 185.30}
        },
        "cash": 10000,
        "total_value": 87500,
        "target_allocation": {"tech": 0.7, "cash": 0.3}
    }
    
    try:
        async with StockAIAgent() as agent:
            optimization = await agent.portfolio_optimization(
                portfolio_data=sample_portfolio,
                optimization_goal="balanced"
            )
            
            print("✅ Portfolio optimization completed!")
            print(f"📅 Generated at: {optimization['generated_at']}")
            print(f"🎯 Goal: {optimization['goal']}")
            
            # Show optimization snippet
            opt_snippet = optimization['optimization_result'][:250]
            print(f"\n📊 Optimization Result Snippet:")
            print(f"{opt_snippet}...")
            
    except Exception as e:
        print(f"❌ Error in portfolio optimization: {e}")

def check_setup():
    """Check if required environment variables are set up"""
    print("🔍 Checking setup...")
    
    required_vars = ["GITHUB_TOKEN"]  # GitHub Models is easiest to start with
    optional_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: Set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var}: Set")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {missing_required}")
        print("📝 Please create a .env file and add your API keys")
        print("💡 For GitHub Models, get a token from: https://github.com/settings/tokens")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Optional variables not set: {missing_optional}")
        print("💡 These are needed for Azure AI Foundry integration")
    
    return True

async def main():
    """Main demo function"""
    
    print("🚀 AI Stock Agent Integration Demo")
    print("🤖 GPT-5, Azure AI Foundry, and Multiple AI Models")
    print("=" * 60)
    
    if not check_setup():
        print("\n❌ Setup incomplete. Please configure your API keys.")
        return
    
    print("\n🎯 Available Models:")
    from config.ai_models_config import ai_models
    models = ai_models.list_available_models()
    for key, name in models.items():
        print(f"  • {key}: {name}")
    
    # Run demos
    await demo_stock_analysis()
    await demo_strategy_generation() 
    await demo_portfolio_optimization()
    
    print("\n\n🎉 Demo completed!")
    print("💡 Next steps:")
    print("  1. Set up your .env file with API keys")
    print("  2. Connect to your SQL Server database")
    print("  3. Integrate with real-time stock data feeds")
    print("  4. Customize the AI prompts for your specific needs")
    print("  5. Add your own trading strategies and risk management rules")

if __name__ == "__main__":
    asyncio.run(main())