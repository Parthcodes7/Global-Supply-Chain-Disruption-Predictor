@echo off
TITLE Global Supply Chain Disruption Predictor
echo =====================================================================
echo  ORCA-GIS // Global Supply Chain Disruption Predictor
echo  VIT Pune DBMS Academic Prototype (MySQL 8.0 Spatial Engine)
echo =====================================================================
echo.

REM Check if MySQL on port 3307 is running
netstat -ano | findstr :3307 >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] MySQL Server is already running on port 3307.
) else (
    echo [STARTING] Launching isolated MySQL instance on port 3307...
    start "MySQL 8.0 Instance (Port 3307)" /B "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="e:\DBMS\mysql_data" --port=3307 --mysqlx=0 --console
    timeout /t 3 /nobreak >nul
)

echo.
echo [STARTING] Launching FastAPI Web Dashboard on http://127.0.0.1:8000...
start "" http://127.0.0.1:8000/
python backend\server.py

pause
