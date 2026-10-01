@echo off
title Launching Phase 1 Blender
cd /d "%~dp0"
start "" "%~dp0toolchain\blender\blender.exe" "%~dp0tools\demolishor\demolishor_phase1.blend"
exit /b 0
