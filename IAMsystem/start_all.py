#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IAM系统所有模块一键启动脚本
支持同时启动审计追溯、委托授权、身份注册三个核心模块
兼容Windows/Linux/macOS
"""
import os
import sys
import time
import signal
import multiprocessing
from typing import List, Dict

# 模块配置
MODULES = [
    {
        "name": "审计追溯模块",
        "dir": "Audit_Traceability",
        "port": 9000,
        "health_check": "/IAMsystem/audit/health",
        "description": "负责审计日志记录、异常检测、黑名单管理"
    },
    {
        "name": "委托授权模块",
        "dir": "Delegated_Authorization",
        "port": 9001,
        "health_check": "/IAMsystem/auth/health",
        "description": "负责Token签发、校验、撤销，权限委托管理"
    },
    {
        "name": "身份注册模块",
        "dir": "Identity_Registration",
        "port": 9002,
        "health_check": "/IAMsystem/identity/health",
        "description": "负责用户和Bot身份注册、身份校验"
    },
    {
        "name": "管理后台模块",
        "dir": "Admin",
        "port": 9005,
        "health_check": "/IAMsystem/admin/health",
        "description": "负责后台管理、违规记录查询、系统配置"
    },
    {
        "name": "前端静态服务",
        "dir": "WebPages",
        "port": 9006,
        "health_check": "/",
        "description": "管理前端静态页面服务，访问地址: http://localhost:9006",
        "type": "static"
    }
]

processes: List[multiprocessing.Process] = []

def signal_handler(signum, frame):
    """捕获终止信号，停止所有子进程"""
    print("\n\n收到停止信号，正在关闭所有服务...")
    for p in processes:
        if p.is_alive():
            p.terminate()
            p.join()
    print("所有服务已停止，退出成功")
    sys.exit(0)

def run_module(module_config: Dict):
    """启动单个模块"""
    module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), module_config["dir"])
    os.chdir(module_dir)
    sys.path.insert(0, module_dir)
    
    try:
        import uvicorn
        # 静态文件服务特殊处理
        if module_config.get("type") == "static":
            from fastapi import FastAPI
            from fastapi.staticfiles import StaticFiles
            app = FastAPI(title="前端静态服务")
            # 挂载静态文件到根路径
            app.mount("/", StaticFiles(directory=".", html=True), name="static")
            print(f"✅ {module_config['name']} 启动成功，访问地址: http://localhost:{module_config['port']}")
            print(f"   健康检查: http://localhost:{module_config['port']}{module_config['health_check']}")
            print(f"   描述: {module_config['description']}\n")
            uvicorn.run(app, host="0.0.0.0", port=module_config["port"], log_level="warning")
        else:
            # 导入模块的app并启动
            from main import app
            print(f"{module_config['name']} 启动成功，访问地址: http://localhost:{module_config['port']}")
            print(f"   健康检查: http://localhost:{module_config['port']}{module_config['health_check']}")
            print(f"   描述: {module_config['description']}\n")
            uvicorn.run(app, host="0.0.0.0", port=module_config["port"], log_level="info")
    except Exception as e:
        print(f"{module_config['name']} 启动失败: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    print("=" * 60)
    print("IAM系统 一键启动脚本")
    print("=" * 60)
    print(f"共有 {len(MODULES)} 个核心模块待启动\n")

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动所有模块
    for module in MODULES:
        p = multiprocessing.Process(target=run_module, args=(module,), name=module["name"])
        p.daemon = True
        p.start()
        processes.append(p)
        time.sleep(1)  # 间隔启动避免端口冲突和日志混乱

    print("\n" + "=" * 60)
    print("所有模块已启动完成，按 Ctrl+C 停止所有服务")
    print("=" * 60 + "\n")

    # 等待所有进程结束
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
