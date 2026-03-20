@echo off
REM Testing script untuk AI Reminder Agent
REM Edit TEST_CHAT_ID dan TEST_USER_ID sesuai kebutuhan

REM Pastikan sudah di folder ai-agent
cd /d "%~dp0"

REM Install requests jika belum ada
pip install requests -q 2>nul

REM Run tests
python test.py
