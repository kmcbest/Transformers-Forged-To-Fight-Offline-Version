@echo off
set ROOT=%~dp0
set UNITY_EXE=%ROOT%toolchain\Unity_2020.3.31f1\Editor\Unity.exe
set PROJECT_DIR=%ROOT%toolchain\unity_build_project

echo ====================================================
echo  Launching Unity Editor 2020.3.31f1 Project...
echo  Project: %PROJECT_DIR%
echo ====================================================
start "" "%UNITY_EXE%" -projectPath "%PROJECT_DIR%"
