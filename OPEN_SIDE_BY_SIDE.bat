@echo off
title Launching Side-by-Side Rig Approval Inspector
cd /d "%~dp0"
start "" "%~dp0toolchain\blender\blender.exe" -y "%~dp0tools\demolishor\demolishor_ironhide_side_by_side.blend"
exit /b 0
