"""
Deploy API routes
"""

import os
import io
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import core logic from src
from src.cli import detect_project_type, generate_deploy_script, generate_dockerfile, generate_nginx_config
from web.api.servers import get_server_credentials, load_config

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

@router.get("/list-paths")
async def list_project_paths():
    """Scan common directories and return subdirectory paths"""
    import stat
    
    scan_dirs = ["/www/wwwroot/", "/root/", "/home/"]
    skip_names = {
        "node_modules", "venv", ".venv", "env", "__pycache__",
        ".git", ".svn", ".hg", "cache", "tmp", "temp", ".cache",
        ".local", ".npm", ".nvm", ".pyenv", ".rbenv", ".rustup",
        ".cargo", ".config", ".ssh", ".aws", ".docker",
    }
    results = []

    for base in scan_dirs:
        if not os.path.isdir(base):
            continue
        try:
            entries = os.listdir(base)
        except PermissionError:
            continue
        for name in sorted(entries):
            if name.startswith(".") or name in skip_names:
                continue
            full = os.path.join(base, name)
            try:
                if os.path.isdir(full):
                    results.append({"path": full, "name": name})
            except (PermissionError, OSError):
                continue

    return results


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


# ============ Remote Deploy (SSE) ============

class RemoteDeployRequest(BaseModel):
    server_index: Optional[int] = None  # Use saved server by index
    # Or provide server info directly
    host: Optional[str] = None
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_content: Optional[str] = None
    script: str  # The deployment script to execute
    project_path: Optional[str] = None


@router.post("/remote")
async def remote_deploy(req: RemoteDeployRequest):
    """Remote deploy via SSH - returns SSE stream of logs"""
    # Resolve server credentials
    if req.server_index is not None:
        config = load_config()
        servers = config.get("servers", [])
        if req.server_index < 0 or req.server_index >= len(servers):
            raise HTTPException(status_code=400, detail="服务器不存在")
        creds = get_server_credentials(servers[req.server_index])
    elif req.host:
        creds = {
            "host": req.host,
            "port": req.port,
            "user": req.user,
            "password": req.password,
            "key_content": req.key_content,
        }
    else:
        raise HTTPException(status_code=400, detail="请选择服务器或提供服务器信息")

    if not req.script.strip():
        raise HTTPException(status_code=400, detail="部署脚本不能为空")

    return StreamingResponse(
        _stream_deploy(creds, req.script, req.project_path),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_deploy(creds: dict, script: str, project_path: Optional[str] = None):
    """Generator that streams deployment logs via SSE"""
    import paramiko

    def _send_event(event_type: str, data: str):
        return f"event: {event_type}\ndata: {data}\n\n"

    # Phase 1: Connecting
    yield _send_event("log", "🔌 正在连接服务器...")
    yield _send_event("status", "connecting")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect in thread to avoid blocking
        loop = asyncio.get_event_loop()

        def _connect():
            connect_kwargs = {
                "hostname": creds["host"],
                "port": creds.get("port", 22),
                "username": creds.get("user", "root"),
                "timeout": 15,
            }
            key_content = creds.get("key_content")
            password = creds.get("password")

            if key_content:
                key_file_obj = io.StringIO(key_content)
                try:
                    pkey = paramiko.RSAKey.from_private_key(key_file_obj)
                except Exception:
                    key_file_obj = io.StringIO(key_content)
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key(key_file_obj)
                    except Exception:
                        key_file_obj = io.StringIO(key_content)
                        pkey = paramiko.ECDSAKey.from_private_key(key_file_obj)
                connect_kwargs["pkey"] = pkey
            elif password:
                connect_kwargs["password"] = password
            else:
                raise RuntimeError("需要提供密码或密钥")

            client.connect(**connect_kwargs)

        await loop.run_in_executor(None, _connect)
        yield _send_event("log", f"✅ 已连接到 {creds['host']}")
        yield _send_event("status", "connected")

        # Phase 2: Upload script
        yield _send_event("log", "📤 正在上传部署脚本...")
        yield _send_event("status", "uploading")

        def _upload_and_exec():
            # Create temp script on remote
            remote_script_path = "/tmp/ai-auto-deploy.sh"

            # Prepend cd command if project_path is given
            full_script = script
            if project_path:
                full_script = f"cd {project_path}\n{script}"

            # Ensure script has bash shebang and set -e
            if not full_script.startswith("#!"):
                full_script = "#!/bin/bash\nset -e\n\n" + full_script

            sftp = client.open_sftp()
            try:
                with sftp.file(remote_script_path, "w") as f:
                    f.write(full_script)
            finally:
                sftp.close()

            # Make executable
            client.exec_command(f"chmod +x {remote_script_path}")

            # Execute script
            stdin, stdout, stderr = client.exec_command(
                f"bash {remote_script_path}",
                timeout=600,
            )

            # Read output in real time
            import select
            output_lines = []

            while True:
                if stdout.channel.recv_ready():
                    line = stdout.readline()
                    if line:
                        output_lines.append(("stdout", line.rstrip()))
                if stdout.channel.recv_stderr_ready():
                    line = stderr.readline()
                    if line:
                        output_lines.append(("stderr", line.rstrip()))

                if stdout.channel.exit_status_ready():
                    # Read remaining
                    while stdout.channel.recv_ready():
                        line = stdout.readline()
                        if line:
                            output_lines.append(("stdout", line.rstrip()))
                    while stdout.channel.recv_stderr_ready():
                        line = stderr.readline()
                        if line:
                            output_lines.append(("stderr", line.rstrip()))
                    break

                if not output_lines:
                    import time
                    time.sleep(0.1)

            exit_code = stdout.channel.recv_exit_status()

            # Cleanup
            client.exec_command(f"rm -f {remote_script_path}")

            return output_lines, exit_code

        results = await loop.run_in_executor(None, _upload_and_exec)
        output_lines, exit_code = results

        yield _send_event("status", "executing")

        # Stream all collected output
        for stream_type, line in output_lines:
            if stream_type == "stderr":
                yield _send_event("log", f"⚠️ {line}")
            else:
                yield _send_event("log", line)

        # Final status
        if exit_code == 0:
            yield _send_event("log", "🎉 部署完成！")
            yield _send_event("status", "success")
        else:
            yield _send_event("log", f"❌ 部署失败 (退出码: {exit_code})")
            yield _send_event("status", "failed")

    except Exception as e:
        yield _send_event("log", f"❌ 错误: {str(e)}")
        yield _send_event("status", "error")
    finally:
        try:
            client.close()
        except Exception:
            pass
        yield _send_event("done", "stream_end")
