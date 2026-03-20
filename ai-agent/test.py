#!/usr/bin/env python3
"""
Test script untuk AI Reminder Agent
Gunakan untuk testing endpoints tanpa WhatsApp
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"
WAHA_API_KEY = "7dde6a37742043d4b961c10ebd1d06d8"

# Test data
TEST_CHAT_ID = "120363xxx@g.us"  # Ganti dengan chat ID yang sebenarnya
TEST_USER_ID = "120363xxx@c.us"  # Ganti dengan user ID yang sebenarnya

def print_response(title, response):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"📨 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def test_health():
    """Test: Health check"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("✅ Health Check", response)
    return response.status_code == 200

def test_webhook_add_task():
    """Test: Add task via webhook"""
    payload = {
        "sessionId": "default",
        "chatId": TEST_CHAT_ID,
        "fromId": TEST_USER_ID,
        "text": "/add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum",
        "senderName": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print_response("📝 Add Task via Webhook", response)
    return response.status_code == 200

def test_webhook_list_tasks():
    """Test: List tasks via webhook"""
    payload = {
        "sessionId": "default",
        "chatId": TEST_CHAT_ID,
        "fromId": TEST_USER_ID,
        "text": "/list",
        "senderName": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print_response("📋 List Tasks via Webhook", response)
    return response.status_code == 200

def test_get_tasks():
    """Test: Get all tasks (REST API)"""
    response = requests.get(f"{BASE_URL}/tasks/{TEST_CHAT_ID}")
    print_response("📊 Get All Tasks (API)", response)
    return response.status_code == 200

def test_get_stats():
    """Test: Get statistics (REST API)"""
    response = requests.get(f"{BASE_URL}/stats/{TEST_CHAT_ID}")
    print_response("📈 Get Statistics (API)", response)
    return response.status_code == 200

def test_help_command():
    """Test: Help command"""
    payload = {
        "sessionId": "default",
        "chatId": TEST_CHAT_ID,
        "fromId": TEST_USER_ID,
        "text": "/help",
        "senderName": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print_response("🆘 Help Command", response)
    return response.status_code == 200

def test_invalid_command():
    """Test: Invalid command (error handling)"""
    payload = {
        "sessionId": "default",
        "chatId": TEST_CHAT_ID,
        "fromId": TEST_USER_ID,
        "text": "/invalidcommand",
        "senderName": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print_response("⚠️  Invalid Command (Error Handling)", response)
    return response.status_code == 200

def main():
    """Run all tests"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     🧪 AI REMINDER AGENT - TEST SUITE                    ║
╚════════════════════════════════════════════════════════════╝

⚠️  PERHATIAN:
   - Ganti TEST_CHAT_ID dan TEST_USER_ID dengan nilai yang sebenarnya
   - Pastikan AI Agent sudah running di http://localhost:8001
   - Pastikan database sudah diinit

Klik Ctrl+C untuk membatalkan.
""")
    
    input("Press Enter to start tests...\n")
    
    tests = [
        ("Health Check", test_health),
        ("Help Command", test_help_command),
        ("Add Task", test_webhook_add_task),
        ("List Tasks", test_webhook_list_tasks),
        ("Get Tasks (API)", test_get_tasks),
        ("Get Statistics", test_get_stats),
        ("Invalid Command", test_invalid_command),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except requests.exceptions.ConnectionError:
            print(f"\n❌ ERROR: Tidak bisa connect ke {BASE_URL}")
            print("   Pastikan AI Agent sudah running!")
            return
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Result: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("✅ All tests passed! AI Agent is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
