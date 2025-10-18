"""
Advanced AI Stock Agent
Multi-model AI agent for comprehensive stock market analysis
"""
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from agents.ai_agent_client import AIAgentClient
from config.ai_models_config import ai_models

class StockAIAgent:
    """
    Advanced AI Agent for Stock Market Analysis
    
    Features:
    - Multi-model AI integration (GPT-5, O3, DeepSeek, Codex)
    - Comprehensive stock analysis (technical, fundamental, sentiment)
    - Automated trading strategy generation
    - Risk assessment and portfolio optimization
    - Real-time market monitoring
    """
    
    def __init__(self):
        self.ai_client: Optional[AIAgentClient] = None
        self.logger = self._setup_logger()
        self.analysis_cache = {}
        
    def _setup_logger(self):
        logger = logging.getLogger("stock_ai_agent")
        logger.setLevel(logging.INFO)
        return logger
        
    async def __aenter__(self):
        self.ai_client = await AIAgentClient().__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ai_client:
            await self.ai_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def comprehensive_stock_analysis(
        self,
        ticker: str,
        stock_data: Dict[str, Any],
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive multi-dimensional stock analysis
        
        Args:
            ticker: Stock ticker symbol
            stock_data: Historical and current stock data
            include_predictions: Whether to include AI predictions
            
        Returns:
            Comprehensive analysis results
        """
        self.logger.info(f"Starting comprehensive analysis for {ticker}")
        
        # Prepare analysis tasks for parallel processing
        analysis_tasks = [
            {
                "name": "technical_analysis",
                "messages": [
                    {"role": "system", "content": self._get_technical_analyst_prompt()},
                    {"role": "user", "content": f"Perform technical analysis for {ticker}:\n{json.dumps(stock_data, indent=2)}"}
                ],
                "model_key": "gpt5_mini"
            },
            {
                "name": "fundamental_analysis", 
                "messages": [
                    {"role": "system", "content": self._get_fundamental_analyst_prompt()},
                    {"role": "user", "content": f"Perform fundamental analysis for {ticker}:\n{json.dumps(stock_data, indent=2)}"}
                ],
                "model_key": "o3"  # Use reasoning model for complex analysis
            },
            {
                "name": "sentiment_analysis",
                "messages": [
                    {"role": "system", "content": self._get_sentiment_analyst_prompt()},
                    {"role": "user", "content": f"Analyze market sentiment for {ticker}:\n{json.dumps(stock_data, indent=2)}"}
                ],
                "model_key": "gpt5"
            },
            {
                "name": "risk_assessment",
                "messages": [
                    {"role": "system", "content": self._get_risk_analyst_prompt()},
                    {"role": "user", "content": f"Assess investment risks for {ticker}:\n{json.dumps(stock_data, indent=2)}"}
                ],
                "model_key": "deepseek_r1"  # Use reasoning model for risk analysis
            }
        ]
        
        if include_predictions:
            analysis_tasks.append({
                "name": "price_prediction",
                "messages": [
                    {"role": "system", "content": self._get_prediction_analyst_prompt()},
                    {"role": "user", "content": f"Predict price movements for {ticker}:\n{json.dumps(stock_data, indent=2)}"}
                ],
                "model_key": "o3"
            })
        
        # Execute all analyses in parallel
        if self.ai_client is None:
            raise RuntimeError("AI client not initialized. Use async context manager.")
        results = await self.ai_client.batch_analysis(analysis_tasks, max_concurrent=3)
        
        # Process results
        analysis_results: Dict[str, Any] = {"ticker": ticker, "timestamp": datetime.now().isoformat()}
        
        for i, task in enumerate(analysis_tasks):
            task_name = task["name"]
            result = results[i]
            
            if result["success"]:
                content = result["result"]["choices"][0]["message"]["content"]
                analysis_results[task_name] = self._parse_analysis_result(content, task_name)
            else:
                self.logger.error(f"Failed {task_name} for {ticker}: {result['error']}")
                analysis_results[task_name] = {"error": result["error"]}
        
        # Generate final recommendation
        analysis_results["final_recommendation"] = await self._generate_final_recommendation(
            ticker, analysis_results
        )
        
        return analysis_results
    
    async def generate_trading_strategy(
        self,
        strategy_requirements: str,
        risk_tolerance: str = "moderate",
        timeframe: str = "medium_term"
    ) -> Dict[str, Any]:
        """
        Generate custom trading strategy using AI
        
        Args:
            strategy_requirements: Description of desired strategy
            risk_tolerance: low, moderate, high
            timeframe: short_term, medium_term, long_term
            
        Returns:
            Generated trading strategy with code and documentation
        """
        self.logger.info("Generating trading strategy")
        
        strategy_prompt = f"""
        Generate a comprehensive trading strategy with the following requirements:
        
        Requirements: {strategy_requirements}
        Risk Tolerance: {risk_tolerance}
        Timeframe: {timeframe}
        
        Include:
        1. Strategy overview and logic
        2. Entry and exit rules
        3. Risk management rules
        4. Python implementation
        5. Backtesting framework
        6. Performance metrics to track
        """
        
        messages = [
            {"role": "system", "content": self._get_strategy_generator_prompt()},
            {"role": "user", "content": strategy_prompt}
        ]
        
        # Use Codex for code generation
        if self.ai_client is None:
            raise RuntimeError("AI client not initialized. Use async context manager.")
        strategy_response = await self.ai_client.chat_completion(
            messages, model_key="codex_mini", temperature=0.2
        )
        
        strategy_content = strategy_response["choices"][0]["message"]["content"]
        
        # Generate additional documentation
        doc_messages = [
            {"role": "system", "content": "You are a financial documentation expert."},
            {"role": "user", "content": f"Create detailed documentation for this trading strategy:\n\n{strategy_content}"}
        ]
        
        doc_response = await self.ai_client.chat_completion(
            doc_messages, model_key="gpt5_mini"
        )
        
        return {
            "strategy_code": strategy_content,
            "documentation": doc_response["choices"][0]["message"]["content"],
            "generated_at": datetime.now().isoformat(),
            "requirements": strategy_requirements,
            "risk_tolerance": risk_tolerance,
            "timeframe": timeframe
        }
    
    async def portfolio_optimization(
        self,
        portfolio_data: Dict[str, Any],
        optimization_goal: str = "maximize_return"
    ) -> Dict[str, Any]:
        """
        AI-powered portfolio optimization
        
        Args:
            portfolio_data: Current portfolio holdings and market data
            optimization_goal: maximize_return, minimize_risk, balanced
            
        Returns:
            Optimized portfolio allocation recommendations
        """
        self.logger.info("Performing portfolio optimization")
        
        optimization_prompt = f"""
        Optimize this portfolio based on the goal: {optimization_goal}
        
        Current Portfolio Data:
        {json.dumps(portfolio_data, indent=2)}
        
        Provide:
        1. Recommended asset allocation
        2. Rebalancing suggestions
        3. Risk analysis
        4. Expected return estimates
        5. Diversification improvements
        """
        
        messages = [
            {"role": "system", "content": self._get_portfolio_optimizer_prompt()},
            {"role": "user", "content": optimization_prompt}
        ]
        
        if self.ai_client is None:
            raise RuntimeError("AI client not initialized. Use async context manager.")
        response = await self.ai_client.chat_completion(
            messages, model_key="o3", temperature=0.3
        )
        
        return {
            "optimization_result": response["choices"][0]["message"]["content"],
            "goal": optimization_goal,
            "generated_at": datetime.now().isoformat()
        }
    
    async def market_monitoring_agent(
        self,
        watchlist: List[str],
        alert_conditions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        AI-powered market monitoring and alert system
        
        Args:
            watchlist: List of tickers to monitor
            alert_conditions: Conditions that trigger alerts
            
        Returns:
            List of alerts and recommendations
        """
        self.logger.info(f"Monitoring {len(watchlist)} stocks")
        
        alerts = []
        
        for ticker in watchlist:
            # This would integrate with real-time data feeds
            # For now, we'll simulate with the monitoring logic
            
            monitor_prompt = f"""
            Monitor {ticker} for the following conditions:
            {json.dumps(alert_conditions, indent=2)}
            
            Analyze current market conditions and determine if any alerts should be triggered.
            Provide actionable recommendations if alerts are found.
            """
            
            messages = [
                {"role": "system", "content": self._get_monitor_prompt()},
                {"role": "user", "content": monitor_prompt}
            ]
            
            if self.ai_client is None:
                raise RuntimeError("AI client not initialized. Use async context manager.")
            response = await self.ai_client.chat_completion(
                messages, model_key="gpt5_nano", temperature=0.1  # Fast, precise monitoring
            )
            
            alert_result = response["choices"][0]["message"]["content"]
            
            alerts.append({
                "ticker": ticker,
                "analysis": alert_result,
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _parse_analysis_result(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI analysis result into structured format"""
        # This would implement proper parsing logic based on analysis type
        # For now, return the raw content with metadata
        return {
            "content": content,
            "type": analysis_type,
            "confidence": "high",  # Would be calculated based on model confidence
            "key_points": self._extract_key_points(content)
        }
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from analysis content"""
        # Simple implementation - would be more sophisticated in practice
        lines = content.split('\n')
        key_points = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommendation', 'key', 'important', 'critical', 'buy', 'sell', 'hold']):
                key_points.append(line.strip())
        
        return key_points[:5]  # Return top 5 key points
    
    async def _generate_final_recommendation(
        self,
        ticker: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate final investment recommendation based on all analyses"""
        
        summary_prompt = f"""
        Based on the following comprehensive analysis for {ticker}, provide a final investment recommendation:
        
        Technical Analysis: {analysis_results.get('technical_analysis', {}).get('content', 'N/A')}
        Fundamental Analysis: {analysis_results.get('fundamental_analysis', {}).get('content', 'N/A')}
        Sentiment Analysis: {analysis_results.get('sentiment_analysis', {}).get('content', 'N/A')}
        Risk Assessment: {analysis_results.get('risk_assessment', {}).get('content', 'N/A')}
        
        Provide:
        1. Overall recommendation (Strong Buy, Buy, Hold, Sell, Strong Sell)
        2. Confidence level (1-10)
        3. Key reasoning
        4. Suggested position size
        5. Stop loss and target levels
        """
        
        messages = [
            {"role": "system", "content": "You are a senior investment advisor providing final recommendations."},
            {"role": "user", "content": summary_prompt}
        ]
        
        if self.ai_client is None:
            raise RuntimeError("AI client not initialized. Use async context manager.")
        response = await self.ai_client.chat_completion(
            messages, model_key="o3", temperature=0.2
        )
        
        return {
            "recommendation": response["choices"][0]["message"]["content"],
            "generated_at": datetime.now().isoformat()
        }
    
    # System prompts for different AI roles
    def _get_technical_analyst_prompt(self) -> str:
        return """You are a senior technical analyst with 20+ years of experience in stock market analysis.
        Focus on chart patterns, technical indicators, support/resistance levels, volume analysis, and momentum indicators.
        Provide specific entry/exit points and price targets with reasoning."""
    
    def _get_fundamental_analyst_prompt(self) -> str:
        return """You are a fundamental analyst specializing in company valuation and financial statement analysis.
        Analyze financial ratios, growth prospects, competitive position, and intrinsic value.
        Consider macroeconomic factors and industry trends."""
    
    def _get_sentiment_analyst_prompt(self) -> str:
        return """You are a market sentiment analyst tracking investor behavior and market psychology.
        Analyze news sentiment, social media trends, institutional flows, and market positioning.
        Assess how sentiment might impact price movements."""
    
    def _get_risk_analyst_prompt(self) -> str:
        return """You are a risk management specialist focused on identifying and quantifying investment risks.
        Analyze volatility, correlation, liquidity risks, and potential downside scenarios.
        Provide risk-adjusted return expectations and hedging suggestions."""
    
    def _get_prediction_analyst_prompt(self) -> str:
        return """You are a quantitative analyst specializing in price prediction models.
        Use statistical analysis, pattern recognition, and market dynamics to forecast price movements.
        Provide probability-weighted scenarios for different time horizons."""
    
    def _get_strategy_generator_prompt(self) -> str:
        return """You are an algorithmic trading strategist and Python developer.
        Create robust, well-documented trading strategies with proper risk management.
        Include backtesting framework and performance monitoring capabilities."""
    
    def _get_portfolio_optimizer_prompt(self) -> str:
        return """You are a portfolio manager specializing in modern portfolio theory and optimization.
        Apply risk-return optimization, diversification principles, and correlation analysis.
        Consider transaction costs and practical implementation constraints."""
    
    def _get_monitor_prompt(self) -> str:
        return """You are a market monitoring system focused on identifying actionable trading opportunities.
        Analyze real-time market conditions against predefined criteria.
        Provide clear, concise alerts with specific action recommendations."""

# Utility functions
async def analyze_stock(ticker: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick stock analysis function"""
    async with StockAIAgent() as agent:
        return await agent.comprehensive_stock_analysis(ticker, stock_data)

async def generate_strategy(requirements: str) -> Dict[str, Any]:
    """Quick strategy generation function"""
    async with StockAIAgent() as agent:
        return await agent.generate_trading_strategy(requirements)