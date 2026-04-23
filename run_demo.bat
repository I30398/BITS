@echo off
echo ================================================
echo Distributed Chat Room Demo
echo ================================================
echo.
echo Please run each command in a SEPARATE terminal:
echo.
echo Terminal 1 (File Server):
echo   python file_server.py
echo.
echo Terminal 2 (Client - Lucy):
echo   python chat_client.py node1 Lucy
echo.
echo Terminal 3 (Client - Joel):
echo   python chat_client.py node2 Joel
echo.
echo ================================================
echo.
echo Starting File Server...
python file_server.py
