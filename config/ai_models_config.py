"""
AI Models Configuration for AI Stock Project
Supports GPT-5, Azure AI Foundry, and GitHub Models integration
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AIProvider(Enum):
    GITHUB_MODELS = "github"
    AZURE_AI_FOUNDRY = "azure_foundry"
    OPENAI_DIRECT = "openai"
    AZURE_OPENAI = "azure_openai"

@dataclass
class ModelConfig:
    """Configuration for AI model connection"""
    provider: AIProvider
    model_name: str
    api_key: str
    endpoint: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    
class AIModelsManager:
    """Centralized AI Models Manager for Stock Analysis"""
    
    def __init__(self):
        self.models = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default model configurations"""
        
        # GPT-5 via GitHub Models (Free tier available)
        self.models['gpt5'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="openai/gpt-5",
            api_key=os.getenv("GITHUB_TOKEN", ""),  # GitHub Personal Access Token
            endpoint="https://models.github.ai/inference/",
            max_tokens=100000,  # GPT-5 supports 200K context
            temperature=0.3  # Lower for financial analysis
        )
        
        # GPT-5 Mini for faster operations
        self.models['gpt5_mini'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="openai/gpt-5-mini",
            api_key=os.getenv("GITHUB_TOKEN", ""),
            endpoint="https://models.github.ai/inference/",
            max_tokens=100000,
            temperature=0.2
        )
        
        # GPT-5 Nano for ultra-fast operations
        self.models['gpt5_nano'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="openai/gpt-5-nano",
            api_key=os.getenv("GITHUB_TOKEN", ""),
            endpoint="https://models.github.ai/inference/",
            max_tokens=100000,
            temperature=0.1
        )
        
        # Codex Mini for code generation
        self.models['codex_mini'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="openai/codex-mini",
            api_key=os.getenv("GITHUB_TOKEN", ""),
            endpoint="https://models.github.ai/inference/",
            max_tokens=100000,
            temperature=0.1
        )
        
        # Azure AI Foundry Configuration (Your deployment)
        self.models['azure_gpt5'] = ModelConfig(
            provider=AIProvider.AZURE_OPENAI,
            model_name="gpt-5-chat",
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat-11"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            max_tokens=16000,  # Azure GPT-5 supports max 16,384 tokens
            temperature=0.3
        )
        
        # o3 for advanced reasoning (financial analysis)
        self.models['o3'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="openai/o3",
            api_key=os.getenv("GITHUB_TOKEN", ""),
            endpoint="https://models.github.ai/inference/",
            max_tokens=100000,
            temperature=0.2
        )
        
        # DeepSeek R1 for reasoning tasks
        self.models['deepseek_r1'] = ModelConfig(
            provider=AIProvider.GITHUB_MODELS,
            model_name="deepseek/deepseek-r1",
            api_key=os.getenv("GITHUB_TOKEN", ""),
            endpoint="https://models.github.ai/inference/",
            max_tokens=4000,
            temperature=0.3
        )
    
    def get_model_config(self, model_key: str) -> ModelConfig:
        """Get model configuration by key"""
        if model_key not in self.models:
            raise ValueError(f"Model '{model_key}' not found. Available models: {list(self.models.keys())}")
        return self.models[model_key]
    
    def add_custom_model(self, key: str, config: ModelConfig):
        """Add custom model configuration"""
        self.models[key] = config
    
    def list_available_models(self) -> Dict[str, str]:
        """List all available models with their names"""
        return {key: config.model_name for key, config in self.models.items()}

# Global instance
ai_models = AIModelsManager()