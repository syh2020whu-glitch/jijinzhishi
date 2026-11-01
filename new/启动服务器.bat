@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo   吉金智識 · 本地服务
echo   ================================

REM 依次尝试常见的 Python 入口
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if not defined PY if exist "C:\Python313\python.exe" set "PY=C:\Python313\python.exe"
if not defined PY if exist "C:\Python312\python.exe" set "PY=C:\Python312\python.exe"
if not defined PY if exist "C:\Python311\python.exe" set "PY=C:\Python311\python.exe"
REM Administrator 账户下装的 Python（本机权限允许时可读）
if not defined PY if exist "C:\Users\kelly\AppData\Local\Programs\Python\Python313\python.exe" set "PY=C:\Users\kelly\AppData\Local\Programs\Python\Python313\python.exe"
if not defined PY if exist "C:\Users\kelly\AppData\Local\Programs\Python\Python312\python.exe" set "PY=C:\Users\kelly\AppData\Local\Programs\Python\Python312\python.exe"
if not defined PY if exist "C:\Users\kelly\AppData\Local\Programs\Python\Python311\python.exe" set "PY=C:\Users\kelly\AppData\Local\Programs\Python\Python311\python.exe"

if not defined PY (
    echo.
    echo   ✗ 找不到 Python
    echo.
    echo   请任选其一装好 Python 后再运行本脚本：
    echo     A. 到 https://www.python.org/downloads/ 下载安装
    echo        安装时务必勾选 "Add python.exe to PATH"
    echo     B. Microsoft Store 搜索 "Python 3.12" 一键安装
    echo.
    pause
    exit /b 1
)

echo   Python : %PY%
echo   网站   : http://localhost:8080/demo.html
echo   识图   : 读 ocr-endpoint.json，打到远端 /ocr
echo   本机 GPU 自建后端才用：启动识图.bat
echo   ================================
echo.
echo   ▶ 服务启动后请浏览器打开 http://localhost:8080/demo.html
echo     关闭本窗口 = 关闭服务
echo.

"%PY%" serve.py

echo.
echo   服务已停止
pause
