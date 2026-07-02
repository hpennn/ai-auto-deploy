"""
Server management API routes
"""

import os
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

CONFIG_FILE = os.path.expanduser("~/.ai-deploy.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"servers": [], "defaults": {}}


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


class ServerCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None
    baota: bool = False
    baota_port: Optional[str] = None
    baota_path: Optional[str] = None


@router.get("")
async def list_servers():
    """Get all saved servers"""
    config = load_config()
    return {"servers": config.get("servers", [])}


@router.post("")
async def add_server(server: ServerCreate):
    """Add a new server"""
    config = load_config()

    server_dict = server.dict()
    # Remove None values
    server_dict = {k: v for k, v in server_dict.items() if v is not None}

    config["servers"].append(server_dict)
    save_config(config)

    return {"message": "服务器已添加", "server": server_dict}


@router.delete("/{index}")
async def delete_server(index: int):
    """Delete a server by index"""
    config = load_config()
    servers = config.get("servers", [])

    if index < 0 or index >= len(servers):
        raise HTTPException(status_code=404, detail="服务器不存在")

    removed = servers.pop(index)
    config["servers"] = servers
    save_config(config)

    return {"message": "服务器已删除", "server": removed}
