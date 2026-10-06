@echo off
chcp 65001 >nul
title 同步并部署至 GitHub Pages
cd /d "%~dp0"

echo [1/2] 正在拉取线上最新编辑、导出静态数据并生成 bots.html...
python tools/sync_web_to_github_io.py
if %errorlevel% neq 0 (
    echo [错误] 同步处理失败！
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] 正在提交并推送到 GitHub Pages (kmcbest.github.io)...
cd /d D:\docforall\GitHub\kmcbest.github.io
git add tftfr/
git commit -m "update tftfr web and static cache"
git push

echo.
echo [提示] 部署完成！云端 Upstash KV 数据已受保护（未发生任何反向推送覆盖）。
pause
