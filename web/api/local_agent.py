from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class GenerateScriptRequest(BaseModel):
    method: str  # coze_desktop / docker / source
    config: Dict[str, Any]


class InstallGuideRequest(BaseModel):
    env_type: str  # docker / git / coze / python


# ====== 方案元信息（前端已有，这里提供后端补充） ======
METHODS_META = {
    "coze_desktop": {
        "name": "Coze 桌面客户端",
        "difficulty": "easy",
        "description": "通过 Coze 桌面客户端绑定本地设备，零代码部署",
    },
    "docker": {
        "name": "Docker 一键部署",
        "difficulty": "medium",
        "description": "使用 Docker Compose 部署开源版 Coze Studio",
    },
    "source": {
        "name": "源码手动部署",
        "difficulty": "hard",
        "description": "从源码构建并运行 Coze Agent",
    },
}


@router.get("/compare-methods")
async def compare_methods():
    """返回三种本地部署方案的对比信息"""
    return {
        "ok": True,
        "methods": METHODS_META,
        "comparison": {
            "coze_desktop": {
                "time": "5-10分钟",
                "requirements": ["Windows 10+ / macOS 10.15+", "Coze 桌面客户端"],
                "pros": ["零代码", "官方支持", "自动更新"],
                "cons": ["依赖网络", "定制性有限"],
            },
            "docker": {
                "time": "15-30分钟",
                "requirements": ["Docker 20.10+", "Docker Compose v2+", "4GB+ 内存"],
                "pros": ["隔离环境", "一键启动", "易迁移"],
                "cons": ["需要 Docker 基础", "占用资源较多"],
            },
            "source": {
                "time": "30-60分钟",
                "requirements": ["Git", "Python 3.10+", "Node.js 18+", "4GB+ 内存"],
                "pros": ["完全掌控", "深度定制", "便于调试"],
                "cons": ["配置复杂", "需要开发经验"],
            },
        },
    }


@router.post("/generate-script")
async def generate_script(req: GenerateScriptRequest):
    """根据用户选择的方案和配置，生成部署脚本"""
    method = req.method
    config = req.config

    if method not in METHODS_META:
        raise HTTPException(status_code=400, detail=f"不支持的部署方案: {method}")

    project_name = config.get("project_name", "my-coze-agent")
    project_path = config.get("project_path", f"/opt/{project_name}")
    port = config.get("port", "8080")
    api_key = config.get("api_key", "")
    docker_image = config.get("docker_image", "coze/coze-studio:latest")

    scripts = {
        "coze_desktop": f"""#!/usr/bin/env powershell
# ============================================
# Coze 桌面客户端 - 本地 Agent 部署脚本
# 方案：通过 Coze 桌面客户端绑定本地设备
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Coze 桌面客户端 - 本地 Agent 部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: 检查是否已安装 Coze 桌面客户端
$cozePath = "$env:LOCALAPPDATA\\Programs\\coze\\coze.exe"
if (-not (Test-Path $cozePath)) {{
    Write-Host "[提示] 未检测到 Coze 桌面客户端" -ForegroundColor Yellow
    Write-Host "请访问 https://www.coze.cn 下载安装" -ForegroundColor Yellow
    Start-Process "https://www.coze.cn"
    exit 1
}}

Write-Host "[OK] Coze 桌面客户端已安装" -ForegroundColor Green

# Step 2: 提示用户操作
Write-Host ""
Write-Host "请按以下步骤操作：" -ForegroundColor Cyan
Write-Host "  1. 打开 Coze 桌面客户端"
Write-Host "  2. 登录你的 Coze 账号"
Write-Host "  3. 进入「设置」→「设备管理」"
Write-Host "  4. 点击「绑定当前设备」"
Write-Host "  5. 在 Coze 平台选择 Agent 并部署到本机"
Write-Host ""
Write-Host "Agent 名称: {agent_name}" -ForegroundColor Green
Write-Host "项目路径:   {project_path}" -ForegroundColor Green

# Step 3: 启动 Coze 客户端
Start-Process $cozePath
Write-Host "[完成] Coze 客户端已启动，请在客户端中完成配置" -ForegroundColor Green
""".format(
            agent_name=config.get("agent_name", "未指定"),
            project_path=project_path,
        ),
        "docker": f"""#!/bin/bash
# ============================================
# Docker 一键部署 - Coze Studio 开源版
# 项目: {project_name}
# 端口: {port}
# ============================================

set -e

echo "========================================"
echo "  Docker 一键部署 Coze Studio"
echo "========================================"

PROJECT_NAME="{project_name}"
PROJECT_PATH="{project_path}"
PORT="{port}"
DOCKER_IMAGE="{docker_image}"

# Step 1: 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker 未安装，请先安装 Docker"
    echo "  Windows/macOS: 下载 Docker Desktop"
    echo "  Linux: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
echo "[OK] Docker 已安装: $(docker --version)"

# Step 2: 检查 Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "[WARN] Docker Compose 插件未检测到，尝试安装..."
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
fi
echo "[OK] Docker Compose 可用"

# Step 3: 创建项目目录
mkdir -p "$PROJECT_PATH"
cd "$PROJECT_PATH"
echo "[OK] 项目目录: $PROJECT_PATH"

# Step 4: 生成 docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'
services:
  coze-studio:
    image: {docker_image}
    container_name: {project_name}
    ports:
      - "{port}:8080"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - API_KEY={api_key}
      - PORT=8080
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
COMPOSE

echo "[OK] docker-compose.yml 已生成"

# Step 5: 创建数据和配置目录
mkdir -p data config
echo "[OK] 数据目录已创建"

# Step 6: 拉取镜像并启动
echo "[INFO] 正在拉取镜像 $DOCKER_IMAGE ..."
docker compose pull

echo "[INFO] 正在启动服务..."
docker compose up -d

echo ""
echo "========================================"
echo "  部署完成！"
echo "  访问地址: http://localhost:{port}"
echo "  查看日志: cd {project_path} && docker compose logs -f"
echo "  停止服务: cd {project_path} && docker compose down"
echo "========================================"
""",
        "source": f"""#!/bin/bash
# ============================================
# 源码手动部署 - Coze Agent
# 项目: {project_name}
# 路径: {project_path}
# 端口: {port}
# ============================================

set -e

echo "========================================"
echo "  源码部署 Coze Agent"
echo "========================================"

PROJECT_NAME="{project_name}"
PROJECT_PATH="{project_path}"
PORT="{port}"
API_KEY="{api_key}"

# Step 1: 检查依赖
echo "[1/7] 检查依赖..."

check_cmd() {{
    if ! command -v $1 &> /dev/null; then
        echo "[ERROR] $1 未安装"
        exit 1
    fi
    echo "  [OK] $1: $($1 --version 2>&1 | head -1)"
}}

check_cmd git
check_cmd python3
check_cmd node
check_cmd pnpm

# Step 2: 克隆源码
echo "[2/7] 克隆源码..."
mkdir -p "$PROJECT_PATH"
cd "$PROJECT_PATH"

if [ ! -d ".git" ]; then
    git clone https://github.com/anthropics/coze-studio.git .
    echo "  [OK] 源码已克隆"
else
    echo "  [OK] 源码目录已存在，执行 git pull"
    git pull
fi

# Step 3: 创建虚拟环境
echo "[3/7] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate
echo "  [OK] 虚拟环境已激活"

# Step 4: 安装后端依赖
echo "[4/7] 安装后端依赖..."
pip install -r requirements.txt
echo "  [OK] 后端依赖安装完成"

# Step 5: 安装前端依赖
echo "[5/7] 安装前端依赖..."
cd frontend
pnpm install
cd ..
echo "  [OK] 前端依赖安装完成"

# Step 6: 配置环境变量
echo "[6/7] 配置环境变量..."
cat > .env << ENV
# Coze Agent 配置
API_KEY=$API_KEY
PORT=$PORT
DATABASE_URL=sqlite:///./data/agent.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=info
ENV
echo "  [OK] .env 文件已生成"

# Step 7: 启动服务
echo "[7/7] 启动服务..."

# 启动后端
nohup python -m uvicorn main:app --host 0.0.0.0 --port $PORT > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "  [OK] 后端启动 (PID: $BACKEND_PID)"

# 启动前端
cd frontend
nohup pnpm dev --port 3000 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  [OK] 前端启动 (PID: $FRONTEND_PID)"

echo ""
echo "========================================"
echo "  部署完成！"
echo "  后端地址: http://localhost:$PORT"
echo "  前端地址: http://localhost:3000"
echo "  查看日志: tail -f logs/backend.log"
echo "  停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "========================================"
""",
    }

    script = scripts.get(method, "")
    if not script:
        raise HTTPException(status_code=400, detail=f"生成脚本失败: 未知方案 {method}")

    return {"ok": True, "script": script, "method": method, "meta": METHODS_META[method]}


@router.post("/install-guide")
async def install_guide(req: InstallGuideRequest):
    """返回指定环境类型的安装指南"""
    guides = {
        "docker": {
            "title": "Docker 安装指南",
            "steps": [
                "Windows/macOS: 下载 Docker Desktop (https://www.docker.com/products/docker-desktop/)",
                "Linux (Ubuntu/Debian): curl -fsSL https://get.docker.com | sh",
                "Linux (CentOS/RHEL): curl -fsSL https://get.docker.com | sh",
                "验证安装: docker --version",
                "确保 Docker 服务运行: systemctl start docker",
            ],
            "notes": ["Windows 需要启用 WSL2 或 Hyper-V", "Docker Compose 已内置于 Docker Desktop"],
        },
        "git": {
            "title": "Git 安装指南",
            "steps": [
                "Windows: 下载 Git for Windows (https://git-scm.com/download/win)",
                "macOS: xcode-select --install 或 brew install git",
                "Linux: sudo apt install git (Debian/Ubuntu) 或 sudo yum install git (CentOS/RHEL)",
                "验证安装: git --version",
            ],
            "notes": ["建议使用 Git 2.30 或更高版本"],
        },
        "coze": {
            "title": "Coze 桌面客户端安装指南",
            "steps": [
                "访问 https://www.coze.cn",
                "下载对应系统的桌面客户端（Windows / macOS）",
                "安装并登录 Coze 账号",
                "进入「设置」→「设备管理」→「绑定当前设备」",
            ],
            "notes": ["绑定设备后可在云端直接下发 Agent 到本地运行", "连接失败时检查服务状态，重启电脑后等待自启完成"],
        },
        "python": {
            "title": "Python 安装指南",
            "steps": [
                "Windows: 下载 Python 3.10+ (https://www.python.org/downloads/)，安装时勾选 Add to PATH",
                "macOS: brew install python@3.11",
                "Linux: sudo apt install python3 python3-pip python3-venv",
                "验证安装: python3 --version",
            ],
            "notes": ["建议使用 Python 3.10 或更高版本", "建议使用虚拟环境隔离依赖"],
        },
    }

    guide = guides.get(req.env_type)
    if not guide:
        raise HTTPException(status_code=400, detail=f"未知环境类型: {req.env_type}")

    return {"ok": True, **guide}
