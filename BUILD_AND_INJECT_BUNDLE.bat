@echo off
set ROOT=%~dp0
echo ====================================================
echo  Grafting Demolishor into Game AssetBundle (LZ4)...
echo ====================================================
python "%ROOT%tools\demolishor\generate_demolishor_bundle.py"
pause
