@echo off
cd /d "%~dp0frontend"

npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
