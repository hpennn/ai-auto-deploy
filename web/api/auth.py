"""
AI Auto Deploy - Auth API
用户注册/登录
"""

import hashlib
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web.database import get_db, get_user_by_username, create_user_with_auth

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """简单的密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register(req: RegisterRequest):
    """用户注册"""
    
    # 检查用户名是否已存在
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    
    # 查找用户
    user = get_user_by_username(username)
    if user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    password_hash = hash_password(req.password)
    user_id = create_user_with_auth(username, password_hash)
    
    return {
        "success": True,
        "user_id": user_id,
        "message": "注册成功"
    }


@router.post("/login")
async def login(req: LoginRequest):
    """用户登录"""
    
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    # 查找用户
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")
    
    # 验证密码
    if user.get("password") != hash_password(req.password):
        raise HTTPException(status_code=400, detail="密码错误")
    
    return {
        "success": True,
        "user_id": user["user_id"],
        "message": "登录成功"
    }
