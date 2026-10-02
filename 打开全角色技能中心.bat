@echo off
chcp 65001 >nul
title TFTF 全角色技能中心 Dashboard
cd /d "%~dp0"

echo 正在启动 TFTF 全角色数值与技能中心后端服务...
start "" "http://127.0.0.1:8888"
python tools/db_server.py
pause
