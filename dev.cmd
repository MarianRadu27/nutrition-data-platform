@echo off
cd /d "%~dp0"

start "Nutrition Backend" cmd /k call "%~dp0dev-backend.cmd"
start "Nutrition Frontend" cmd /k call "%~dp0dev-frontend.cmd"

echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:3000
echo.
echo Two terminal windows were opened. Close those windows or press CTRL+C inside them to stop the servers.
