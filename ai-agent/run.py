#!/usr/bin/env python3
"""
Quick run script untuk AI Reminder Agent
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Change to script directory
os.chdir(SCRIPT_DIR)

# Add to path
sys.path.insert(0, str(SCRIPT_DIR))

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║       🤖 AI REMINDER AGENT - WhatsApp Bot v1.0           ║
║                                                           ║
║  Starting FastAPI server on http://0.0.0.0:8001         ║
║  Webhook URL: http://localhost:8001/webhook              ║
║                                                           ║
║  Send /help in WhatsApp to see available commands        ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
