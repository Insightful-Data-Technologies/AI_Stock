# AI Stock Analysis Project 🤖📈

Advanced AI-powered stock market analysis and trading system integrating **GPT-5**, **Azure AI Foundry**, and multiple AI models for comprehensive financial analysis.

## 🚀 Features

### AI Agent Capabilities
- **Multi-Model AI Integration**: GPT-5, O3, DeepSeek R1, Codex Mini
- **Comprehensive Stock Analysis**: Technical, fundamental, sentiment, and risk assessment
- **Automated Trading Strategy Generation**: AI-powered strategy creation with backtesting
- **Portfolio Optimization**: AI-driven portfolio recommendations
- **Real-time Market Monitoring**: Intelligent alerts and notifications
- **Code Generation**: Automated trading algorithm development

### AI Models Available
- **GPT-5** (via GitHub Models): Latest reasoning and analysis
- **GPT-5 Mini/Nano**: Faster versions for real-time operations
- **O3**: Advanced reasoning for complex financial analysis
- **Codex Mini**: Specialized code generation for trading algorithms
- **DeepSeek R1**: Alternative reasoning model
- **Azure AI Foundry**: Enterprise-grade Azure integration

## 🛠️ Quick Setup

### 1. Clone and Initialize
```powershell
git clone https://github.com/Insightful-Data-Technologies/AI_Stock.git
cd AI_Stock
python setup.py
```

### 2. Configure API Keys
Edit `.env` file with your credentials:
```env
# GitHub Models (Free tier available)
GITHUB_TOKEN=your_github_personal_access_token

# Azure AI Foundry (Optional)
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Database
DB_SERVER=LAPTOP-2DEO7474
DB_NAME=AI_Stocks
DB_USERNAME=sa2
DB_PASSWORD=Chanan1234
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Test AI Agent
```powershell
python demo_ai_agent.py
```

## 🤖 AI Agent Usage

### Basic Stock Analysis
```python
import asyncio
from agents.stock_ai_agent import analyze_stock

# Simple analysis
stock_data = {
    "ticker": "AAPL",
    "current_price": 175.25,
    "volume": 45000000,
    "pe_ratio": 28.5
}

result = await analyze_stock("AAPL", stock_data)
print(result['final_recommendation'])
```

### Advanced Multi-Model Analysis
```python
from agents.stock_ai_agent import StockAIAgent

async def advanced_analysis():
    async with StockAIAgent() as agent:
        # Comprehensive analysis using multiple AI models
        analysis = await agent.comprehensive_stock_analysis(
            ticker="AAPL",
            stock_data=stock_data,
            include_predictions=True
        )
        
        # Generate trading strategy
        strategy = await agent.generate_trading_strategy(
            "Create momentum strategy for tech stocks",
            risk_tolerance="moderate"
        )
        
        # Optimize portfolio
        portfolio_opt = await agent.portfolio_optimization(
            portfolio_data=portfolio,
            optimization_goal="maximize_return"
        )
        
        return analysis, strategy, portfolio_opt

results = await advanced_analysis()
```

### Real-time Monitoring
```python
# AI-powered market monitoring
watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA"]
alert_conditions = {
    "price_change": 5.0,  # 5% change
    "volume_spike": 2.0,  # 2x average volume
    "sentiment_shift": "negative"
}

alerts = await agent.market_monitoring_agent(watchlist, alert_conditions)
```

## 🎯 Model Selection Guide

| Task | Recommended Model | Why |
|------|------------------|-----|
| **Quick Analysis** | GPT-5 Nano | Fastest, lowest cost |
| **Deep Analysis** | O3 | Advanced reasoning |
| **Code Generation** | Codex Mini | Specialized for code |
| **Risk Assessment** | DeepSeek R1 | Strong logical reasoning |
| **Real-time Alerts** | GPT-5 Mini | Fast + accurate |
| **Research Reports** | GPT-5 | Best quality output |

## 📊 Database Integration

The project connects to your existing `AI_Stocks` SQL Server database:

```python
# Database tables discovered:
- Stock data: STOCK_RESULTS_ALL, WF_STOCK_RATES
- Predictions: PRED_01_Predictions_Wide, WF03_PREDICT_*
- Configuration: CONF_* tables
- Logging: LOG_* tables
```

## 🏗️ Architecture

```
AI_Stock/
├── agents/                 # AI agent implementations
│   ├── ai_agent_client.py  # Multi-provider AI client
│   └── stock_ai_agent.py   # Stock analysis agent
├── config/                 # Configuration management
│   └── ai_models_config.py # AI model configurations
├── strategies/             # Trading strategies
├── data/                   # Data processing
├── logs/                   # Application logs
└── demo_ai_agent.py        # Demo and examples
```

## 🔧 Configuration

### AI Models Configuration
```python
from config.ai_models_config import ai_models

# List available models
models = ai_models.list_available_models()

# Get specific model config
gpt5_config = ai_models.get_model_config("gpt5")

# Add custom model
ai_models.add_custom_model("my_model", custom_config)
```

### Environment Variables
```env
# AI Configuration
DEFAULT_AI_MODEL=gpt5_mini
AI_MAX_RETRIES=3
AI_TIMEOUT_SECONDS=30
AI_MAX_CONCURRENT_REQUESTS=5

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG_MODE=true
AI_TRACING_ENABLED=true
```

## 🚦 Getting Started Examples

### 1. Single Stock Analysis
```python
python -c "
import asyncio
from agents.stock_ai_agent import analyze_stock

async def quick_test():
    result = await analyze_stock('AAPL', {'current_price': 175})
    print('Recommendation:', result['final_recommendation']['recommendation'][:200])

asyncio.run(quick_test())
"
```

### 2. Strategy Generation
```python
from agents.stock_ai_agent import generate_strategy

strategy = await generate_strategy(
    'Create a mean reversion strategy for large-cap stocks'
)
print(strategy['strategy_code'])
```

### 3. Database Integration
```python
# Connect to your existing database
import pyodbc

conn = pyodbc.connect(
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={DB_SERVER};Database=AI_Stocks;"
    f"UID={DB_USERNAME};PWD={DB_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

# Query your existing data
cursor = conn.execute("SELECT TOP 10 * FROM STOCK_RESULTS_ALL")
data = cursor.fetchall()
```

## 🔑 API Keys Setup

### GitHub Models (Free Tier)
1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Create new token (no special scopes needed)
3. Add to `.env`: `GITHUB_TOKEN=ghp_your_token_here`
4. Free tier: 15,000 tokens/minute per model

### Azure AI Foundry
1. Create Azure OpenAI resource
2. Deploy GPT-5 model
3. Add credentials to `.env`
4. Pay-per-use pricing

## 📈 Performance Optimization

- **Concurrent Processing**: Multiple AI requests in parallel
- **Model Selection**: Choose optimal model for each task
- **Caching**: Results cached for repeated queries
- **Rate Limiting**: Automatic retry with backoff
- **Connection Pooling**: Efficient HTTP connections

## 🛡️ Security Features

- Environment variable management
- API key encryption
- Request rate limiting
- Error handling and logging
- Secure database connections

## 📚 Learning Resources

- [AI Toolkit Documentation](https://aka.ms/vscode-instructions-docs)
- [GitHub Models Guide](https://docs.github.com/en/models)
- [Azure AI Foundry Docs](https://learn.microsoft.com/azure/ai-studio/)
- [Stock Analysis Examples](./notebooks/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/ai-enhancement`
3. Commit changes: `git commit -am 'Add new AI capability'`
4. Push branch: `git push origin feature/ai-enhancement`
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Insightful-Data-Technologies/AI_Stock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Insightful-Data-Technologies/AI_Stock/discussions)
- **Documentation**: Check the `docs/` directory

---

**Built with ❤️ using GPT-5, Azure AI Foundry, and cutting-edge AI models**