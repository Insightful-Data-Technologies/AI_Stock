"""
AI Agent Client for Stock Analysis
Integrates GPT-5, Azure AI Foundry, and various AI models
"""
import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict
import logging
from datetime import datetime

from config.ai_models_config import ai_models, AIProvider, ModelConfig

class AIAgentClient:
    """Advanced AI Agent Client with multiple provider support"""
    
    def __init__(self, default_model: str = "gpt5"):
        self.default_model = default_model
        self.session = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup logging for AI operations"""
        logger = logging.getLogger("ai_agent")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_github_models(self, config: ModelConfig, messages: List[Dict], **kwargs) -> Dict:
        """Call GitHub Models API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": False
        }
        
        async with self.session.post(
            f"{config.endpoint}chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"GitHub Models API error: {response.status} - {error_text}")
            return await response.json()
    
    async def _call_azure_foundry(self, config: ModelConfig, messages: List[Dict], **kwargs) -> Dict:
        """Call Azure AI Foundry API"""
        headers = {
            "api-key": config.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": False
        }
        
        # Azure AI Foundry endpoint format - handle endpoint with/without trailing slash
        base_endpoint = config.endpoint.rstrip('/') if config.endpoint else ""
        url = f"{base_endpoint}/openai/deployments/{config.deployment_name}/chat/completions?api-version={config.api_version}"
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Azure AI Foundry API error: {response.status} - {error_text}")
            return await response.json()
    
    async def _call_azure_openai(self, config: ModelConfig, messages: List[Dict], **kwargs) -> Dict:
        """Call Azure OpenAI API"""
        headers = {
            "api-key": config.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": False
        }
        
        # Azure OpenAI endpoint format - handle endpoint with/without trailing slash
        base_endpoint = (config.endpoint or "").rstrip('/')
        url = f"{base_endpoint}/openai/deployments/{config.deployment_name}/chat/completions?api-version={config.api_version}"
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Azure OpenAI API error: {response.status} - {error_text}")
            return await response.json()
    
    async def chat_completion(
        self, 
        messages: List[Dict], 
        model_key: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Send chat completion request to AI model
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_key: Model key to use (defaults to default_model)
            **kwargs: Additional parameters like max_tokens, temperature
        
        Returns:
            Response dictionary from the API
        """
        model_key = model_key or self.default_model
        config = ai_models.get_model_config(model_key)
        
        self.logger.info(f"Calling model: {config.model_name} via {config.provider.value}")
        
        try:
            if config.provider == AIProvider.GITHUB_MODELS:
                response = await self._call_github_models(config, messages, **kwargs)
            elif config.provider == AIProvider.AZURE_AI_FOUNDRY:
                response = await self._call_azure_foundry(config, messages, **kwargs)
            elif config.provider == AIProvider.AZURE_OPENAI:
                response = await self._call_azure_openai(config, messages, **kwargs)
            else:
                raise ValueError(f"Provider {config.provider} not implemented yet")
            
            self.logger.info("AI request completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"AI request failed: {str(e)}")
            raise
    
    async def analyze_stock_data(
        self,
        stock_data: Dict[str, Any],
        analysis_type: str = "technical",
        model_key: Optional[str] = None
    ) -> str:
        """
        Analyze stock data using AI
        
        Args:
            stock_data: Dictionary containing stock information
            analysis_type: Type of analysis (technical, fundamental, sentiment)
            model_key: AI model to use
        
        Returns:
            Analysis result as string
        """
        system_prompt = self._get_analysis_system_prompt(analysis_type)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this stock data: {json.dumps(stock_data, indent=2)}"}
        ]
        
        # Use reasoning model for complex analysis
        if analysis_type in ["fundamental", "complex"]:
            model_key = model_key or "o3"
        else:
            model_key = model_key or "gpt5_mini"
        
        response = await self.chat_completion(messages, model_key=model_key)
        return response["choices"][0]["message"]["content"]
    
    async def generate_trading_code(
        self,
        requirements: str,
        programming_language: str = "python",
        model_key: Optional[str] = None
    ) -> str:
        """
        Generate trading algorithm code
        
        Args:
            requirements: Description of the trading strategy
            programming_language: Target programming language
            model_key: AI model to use (defaults to codex_mini)
        
        Returns:
            Generated code as string
        """
        system_prompt = f"""You are an expert {programming_language} developer specializing in financial algorithms and trading systems.
        Generate clean, efficient, and well-documented code following best practices.
        Include error handling and proper financial risk management principles."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate {programming_language} code for: {requirements}"}
        ]
        
        model_key = model_key or "codex_mini"
        response = await self.chat_completion(messages, model_key=model_key)
        return response["choices"][0]["message"]["content"]
    
    async def batch_analysis(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Process multiple AI tasks concurrently
        
        Args:
            tasks: List of task dictionaries with 'messages' and optional 'model_key'
            max_concurrent: Maximum concurrent requests
        
        Returns:
            List of results in the same order as input tasks
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_task(task: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.chat_completion(
                        task["messages"], 
                        model_key=task.get("model_key")
                    )
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        results = await asyncio.gather(*[process_task(task) for task in tasks])
        return results
    
    def _get_analysis_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt for different analysis types"""
        prompts = {
            "technical": """You are a professional technical analyst specializing in stock market analysis.
            Analyze the provided stock data focusing on:
            - Price trends and patterns
            - Support and resistance levels  
            - Technical indicators (RSI, MACD, Moving Averages)
            - Volume analysis
            - Chart patterns
            Provide actionable insights and risk assessment.""",
            
            "fundamental": """You are a fundamental analyst with expertise in financial statement analysis.
            Analyze the provided data focusing on:
            - Financial ratios and metrics
            - Company valuation
            - Industry comparison
            - Growth prospects
            - Risk factors
            Provide investment recommendations with reasoning.""",
            
            "sentiment": """You are a market sentiment analyst specializing in news and social media analysis.
            Analyze the provided data for:
            - Market sentiment indicators
            - News impact assessment
            - Social media trends
            - Investor behavior patterns
            Provide sentiment score and market impact prediction."""
        }
        
        return prompts.get(analysis_type, prompts["technical"])

# Utility functions for easy access
async def quick_analysis(stock_data: Dict, analysis_type: str = "technical") -> str:
    """Quick stock analysis function"""
    async with AIAgentClient() as agent:
        return await agent.analyze_stock_data(stock_data, analysis_type)

async def quick_code_generation(requirements: str, language: str = "python") -> str:
    """Quick code generation function"""
    async with AIAgentClient() as agent:
        return await agent.generate_trading_code(requirements, language)