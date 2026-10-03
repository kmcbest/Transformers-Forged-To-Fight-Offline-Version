@echo off
chcp 65001 >nul
title TFTF Fandom 角色数据抓取器
echo 正在启动 TFTF Fandom 角色数据抓取器 (GUI)...
python tools\gui_fandom_scraper.py
pause
