@echo off
chcp 65001 >nul
title 仅更新网页前端到 GitHub Pages (HTML-Only)
cd /d "%~dp0"

echo 正在快速转换网页前端并生成 bots.html...
python tools/sync_web_to_github_io.py --only-html
if %errorlevel% neq 0 (
    echo [错误] 转换失败！
    pause
    exit /b %errorlevel%
)

echo.
echo 正在推送至 GitHub Pages 仓库 (kmcbest.github.io)...
cd /d D:\docforall\GitHub\kmcbest.github.io
git add tftfr/bots.html
git commit -m "update bots.html ui"
git push

echo.
echo [提示] 网页前端已成功推送到 GitHub Pages！
pause
