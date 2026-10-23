@echo off
chcp 65001 >nul
title TFTF 战斗技能沙盒模拟器
echo ========================================================
echo   🤖 TFTF 战斗技能沙盒模拟器 (Combat Ability Simulator)
echo ========================================================
echo.
echo [*] 正在校验/编译 sim_skills.dll ...
python tools\sim\build_sim.py
if errorlevel 1 (
    echo [!] 编译失败，请检查 C 源码错误。
    pause
    exit /b 1
)

echo [*] 启动模拟器 Web 服务 (端口 8088) 并自动打开浏览器...
python tools\sim\sim_server.py 8088
pause
