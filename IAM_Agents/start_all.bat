@echo off
chcp 65001 >nul
echo ============================================================
echo IAM Agents 一键启动脚本 (Windows)
echo ============================================================
echo.
echo 注意：请确保已先启动IAMsystem服务，所有Agent依赖IAM系统认证
echo.

python start_all.py

pause
