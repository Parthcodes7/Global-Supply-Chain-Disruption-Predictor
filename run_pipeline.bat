@echo off
REM =====================================================================
REM Global Supply Chain Disruption Predictor - Automation Runner
REM =====================================================================
echo [INFO] Starting MySQL Automation Pipeline on 127.0.0.1:3307...
python scripts\run_mysql_pipeline.py
echo.
echo [INFO] Pipeline complete. Press any key to exit.
pause
