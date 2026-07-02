"""
Deploy API routes
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import core logic from src
from src.cli import detect_project_type, generate_deploy_script, generate_dockerfile, generate_nginx_config

router = APIRouter()


# ============ Request / Response Models ============

class DetectRequest(BaseModel):
    path: str


class GenerateRequest(BaseModel):
    path: str
    deploy_type: str  # "server" | "cloudflare" | "docker" | "local"
    server: Optional[dict] = None
    domain: Optional[str] = None


class GenerateResponse(BaseModel):
    script: str
    filename: str
    extra_files: Optional[list] = None


# ============ Routes ============

@router.post("/detect")
async def detect_project(req: DetectRequest):
    """Detect project type from a given path"""
    project_path = req.path.strip()

    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")

    try:
        info = detect_project_type(project_path)
        info["project_name"] = os.path.basename(os.path.abspath(project_path))
        info["path"] = project_path
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.post("/generate")
async def generate_script(req: GenerateRequest):
    """Generate deployment script"""
    project_path = req.path.strip()

    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")

    try:
        project_info = detect_project_type(project_path)
        project_name = os.path.basename(os.path.abspath(project_path))
        extra_files = []

        if req.deploy_type == "docker":
            # Generate Dockerfile
            script = generate_dockerfile(project_info)
            filename = "Dockerfile"
        elif req.deploy_type == "cloudflare":
            # Cloudflare Pages deploy
            pm = project_info.get("package_manager") or "npm"
            fw = project_info.get("framework", "")
            output_dir = "dist"
            if fw == "nextjs":
                output_dir = ".next"

            script = f"""#!/bin/bash
# AI Auto Deploy - Cloudflare Pages 部署脚本
# 项目: {project_name}

set -e

echo "🚀 Cloudflare Pages 部署中..."

# 构建
{pm} install --registry=https://registry.npmmirror.com
{pm} run build

# 部署到 Cloudflare Pages
npx wrangler pages deploy {output_dir} --project-name={project_name}

echo "✅ 部署完成！"
"""
            filename = "deploy-cloudflare.sh"
        elif req.deploy_type == "server" and req.server:
            server = req.server
            domain = req.domain or server.get("host", "YOUR_SERVER_IP")
            script = generate_deploy_script(project_info, server, project_name)
            script = script.replace("PROJECT_NAME", project_name)
            filename = "deploy.sh"

            # Also generate nginx config
            nginx_conf = generate_nginx_config(project_info, domain)
            nginx_conf = nginx_conf.replace("PROJECT_NAME", project_name)
            extra_files.append({"filename": "nginx.conf", "content": nginx_conf})
        else:
            # Local script
            server = {"host": "YOUR_SERVER_IP", "baota": False}
            script = generate_deploy_script(project_info, server, project_name)
            script = script.replace("PROJECT_NAME", project_name)
            filename = "deploy.sh"

        return {
            "script": script,
            "filename": filename,
            "extra_files": extra_files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/execute")
async def execute_deploy(req: dict):
    """Execute deployment (optional, requires server access)"""
    return {
        "message": "远程执行功能需要服务器连接配置，请使用生成的脚本手动部署",
        "status": "not_implemented"
    }
