"""
Setup Script for AI Stock Analysis Project
Configures environment and tests AI model connections
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if template_file.exists():
        print("📝 Creating .env file from template...")
        try:
            # Copy template to .env
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ .env file created!")
            print("⚠️  Please edit .env file and add your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.template not found")
        return False

def create_directories():
    """Create necessary project directories"""
    directories = [
        "config",
        "agents", 
        "data",
        "logs",
        "models",
        "strategies",
        "tests",
        "notebooks",
        "static",
        "templates"
    ]
    
    print("📁 Creating project directories...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}/")
    
    return True

async def test_ai_connections():
    """Test connections to AI services"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🧪 Testing AI model connections...")
    
    # Test GitHub Models
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print("✅ GitHub token found")
        try:
            from config.ai_models_config import ai_models
            gpt5_config = ai_models.get_model_config("gpt5_nano")  # Use nano for testing
            print("✅ GPT-5 Nano configuration loaded")
        except Exception as e:
            print(f"⚠️  GPT-5 config error: {e}")
    else:
        print("❌ GitHub token not found in .env")
    
    # Test Azure AI Foundry
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if azure_key and azure_endpoint:
        print("✅ Azure AI Foundry credentials found")
    else:
        print("⚠️  Azure AI Foundry credentials not configured (optional)")
    
    # Test database connection
    db_server = os.getenv("DB_SERVER")
    if db_server:
        print(f"✅ Database server configured: {db_server}")
        # Test actual connection
        try:
            import pyodbc
            conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server={db_server};Database=AI_Stocks;UID=sa2;PWD=Chanan1234;TrustServerCertificate=yes;"
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"⚠️  Database connection failed: {e}")
    else:
        print("❌ Database not configured")

def run_demo():
    """Ask user if they want to run the demo"""
    print("\n🎮 Would you like to run the AI agent demo?")
    response = input("Enter 'y' to run demo, or any other key to skip: ").lower()
    
    if response == 'y':
        print("\n🚀 Running demo...")
        try:
            subprocess.run([sys.executable, "demo_ai_agent.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Demo failed: {e}")
    else:
        print("ℹ️  Demo skipped. You can run it later with: python demo_ai_agent.py")

def show_next_steps():
    """Show user what to do next"""
    print("\n" + "="*60)
    print("🎉 Setup Complete! Next Steps:")
    print("="*60)
    
    print("\n1. 🔑 Configure API Keys:")
    print("   - Edit the .env file")
    print("   - Add your GitHub Personal Access Token")
    print("   - Optionally add Azure AI Foundry credentials")
    
    print("\n2. 📊 Test the AI Agent:")
    print("   - Run: python demo_ai_agent.py")
    
    print("\n3. 🗃️  Connect Your Database:")
    print("   - Verify database credentials in .env")
    print("   - Test connection with your SQL Server")
    
    print("\n4. 📈 Start Building:")
    print("   - Explore the agents/ directory")
    print("   - Customize AI prompts for your needs")
    print("   - Add your trading strategies")
    
    print("\n5. 🚀 Available AI Models:")
    print("   - GPT-5 (via GitHub Models - Free tier)")
    print("   - GPT-5 Mini/Nano (Faster versions)")
    print("   - O3 (Advanced reasoning)")
    print("   - Codex Mini (Code generation)")
    print("   - DeepSeek R1 (Alternative reasoning)")
    
    print("\n💡 Pro Tips:")
    print("   - Start with GitHub Models (free tier)")
    print("   - Use different models for different tasks")
    print("   - GPT-5 Nano is fastest for real-time analysis")
    print("   - O3 is best for complex financial reasoning")
    print("   - Codex Mini excels at generating trading code")

def main():
    """Main setup function"""
    print("🤖 AI Stock Analysis Project Setup")
    print("🔧 Setting up GPT-5, Azure AI Foundry, and AI Agent")
    print("="*60)
    
    # Step 1: Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        return
    
    # Step 2: Create .env file
    if not create_env_file():
        print("❌ Failed to create .env file")
        return
    
    # Step 3: Install dependencies
    print("\n📦 Do you want to install Python dependencies?")
    install_deps = input("Enter 'y' to install, or any other key to skip: ").lower()
    
    if install_deps == 'y':
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            return
    else:
        print("ℹ️  Dependencies skipped. Install later with: pip install -r requirements.txt")
    
    # Step 4: Test connections (if dependencies are installed)
    if install_deps == 'y':
        try:
            asyncio.run(test_ai_connections())
        except ImportError:
            print("⚠️  Skipping connection tests (dependencies not installed)")
        except Exception as e:
            print(f"⚠️  Connection test error: {e}")
    
    # Step 5: Run demo
    if install_deps == 'y':
        run_demo()
    
    # Step 6: Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()