@echo off
TITLE MySQL 8.0 Command Line Client - supply_chain_db
echo =====================================================================
echo  Connecting to MySQL 8.0 Command Line Client
echo  Host: 127.0.0.1 | Port: 3307 | User: root | Database: supply_chain_db
echo =====================================================================
echo.
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -h 127.0.0.1 -P 3307 -u root --database=supply_chain_db --table --prompt="mysql [supply_chain_db]> "
pause
