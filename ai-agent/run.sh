#!/bin/bash
# Quick start script untuk AI Reminder Agent (Linux/macOS)

cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       🤖 AI REMINDER AGENT - WhatsApp Bot v1.0           ║"
echo "║                                                           ║"
echo "║  Starting FastAPI server on http://0.0.0.0:8001         ║"
echo "║  Webhook URL: http://localhost:8001/webhook              ║"
echo "║                                                           ║"
echo "║  Send /help in WhatsApp to see available commands        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

python main.py
