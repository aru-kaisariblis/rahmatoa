#!/usr/bin/env python3
"""
Setup script untuk AI Reminder Agent
Membuat database, install dependencies, dan configure WAHA
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
WAHA_API_URL = "http://localhost:3000"

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    if description:
        print(f"\n▶️  {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to run: {cmd}")
        print(e.stderr)
        return False

def check_python():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version.split()[0]
    print_info(f"Python version: {version}")
    
    major, minor = map(int, version.split('.')[:2])
    if major >= 3 and minor >= 8:
        print_success("Python version is compatible")
        return True
    else:
        print_error("Python 3.8+ required")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    requirements_file = SCRIPT_DIR / "requirements.txt"
    if requirements_file.exists():
        cmd = f"pip install -r {requirements_file}"
        if run_command(cmd, "Installing packages from requirements.txt"):
            print_success("Dependencies installed successfully")
            return True
    else:
        print_error(f"requirements.txt not found at {requirements_file}")
        return False

def create_database():
    """Initialize database"""
    print_header("Initializing Database")
    
    try:
        from utils.database import Database
        db = Database()
        print_success("Database initialized successfully")
        print_info(f"Database path: {db.db_path}")
        return True
    except Exception as e:
        print_error(f"Failed to initialize database: {str(e)}")
        return False

def check_waha_connection():
    """Check connection to WAHA API"""
    print_header("Checking WAHA API Connection")
    
    try:
        response = requests.get(f"{WAHA_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Connected to WAHA API at {WAHA_API_URL}")
            return True
        else:
            print_error(f"WAHA API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to WAHA API at {WAHA_API_URL}")
        print_info("Make sure WAHA bot is running")
        return False
    except Exception as e:
        print_error(f"Error checking WAHA connection: {str(e)}")
        return False

def setup_waha_webhook():
    """Configure WAHA webhook for AI Agent"""
    print_header("Configuring WAHA Webhook")
    
    webhook_url = "http://localhost:8001/webhook"
    print_info(f"Webhook URL: {webhook_url}")
    
    # Check if webhook is already configured
    try:
        response = requests.get(
            f"{WAHA_API_URL}/api/webhooks",
            headers={"X-API-Key": os.getenv("WAHA_API_KEY", "7dde6a37742043d4b961c10ebd1d06d8")},
            timeout=5
        )
        
        if response.status_code == 200:
            webhooks = response.json()
            print_info(f"Current webhooks configured: {len(webhooks)}")
            
            # Check if our webhook already exists
            for webhook in webhooks:
                if webhook.get("url") == webhook_url:
                    print_success("Webhook already configured")
                    return True
        
        # Configure new webhook
        webhook_config = {
            "url": webhook_url,
            "events": ["message"]
        }
        
        response = requests.post(
            f"{WAHA_API_URL}/api/webhooks",
            json=webhook_config,
            headers={"X-API-Key": os.getenv("WAHA_API_KEY", "7dde6a37742043d4b961c10ebd1d06d8")},
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            print_success("Webhook configured successfully")
            print_info("The AI Agent will now receive messages from WAHA")
            return True
        else:
            print_error(f"Failed to configure webhook: {response.status_code}")
            print_info("You can manually configure the webhook through WAHA dashboard")
            return False
    
    except Exception as e:
        print_error(f"Error setting up webhook: {str(e)}")
        print_info("You can manually configure the webhook through WAHA dashboard")
        return False

def print_next_steps():
    """Print next steps"""
    print_header("Next Steps")
    
    print("""
1. Start the AI Agent:
   cd ai-agent
   python main.py

2. Upload your AI Agent publicly (optional, for webhooks):
   If running locally, make sure port 8001 is accessible

3. Test the agent in your WhatsApp group:
   /help              - Show available commands
   /add ...           - Add a new task
   /list              - Show all tasks

4. Check the documentation:
   cat README.md

Need help?
   Read README.md for detailed documentation and examples
""")

def main():
    """Main setup flow"""
    print_header("AI Reminder Agent - Setup")
    
    steps = [
        ("Python Version Check", check_python),
        ("Install Dependencies", install_dependencies),
        ("Initialize Database", create_database),
        ("Check WAHA Connection", check_waha_connection),
        ("Configure Webhook", setup_waha_webhook),
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except KeyboardInterrupt:
            print("\n\n❌ Setup interrupted by user")
            return
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {str(e)}")
            results.append((step_name, False))
    
    # Print summary
    print_header("Setup Summary")
    for step_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {step_name}")
    
    all_success = all(result for _, result in results)
    
    if all_success:
        print_success("Setup completed successfully!")
        print_next_steps()
    else:
        print_error("Setup completed with some errors")
        print_info("Please check the errors above and try again")

if __name__ == "__main__":
    main()
