@echo off
title Launching Phase 2.5 Inspector Blender
cd /d "%~dp0"
start "" "%~dp0toolchain\blender\blender.exe" -y "%~dp0tools\demolishor\demolishor_phase2_inspect.blend"
exit /b 0
