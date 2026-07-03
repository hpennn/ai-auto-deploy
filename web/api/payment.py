"""
Payment API routes - 虎皮椒支付集成
"""

import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from web.database import (
    create_order, update_order_status, get_order,
    get_user, upsert_user, is_paid,
)

router = APIRouter()

# 虎皮椒支付配置
XUNHU_APPID = "201906182239"
XUNHU_APPSECRET = "a03834403fd0101fb1c622545967b3db"
XUNHU_API = "https://api.xunhupay.com"

# 价格配置：月付 99 元，年付 666 元
PRICES = {
    "monthly": 99.0,
    "yearly": 666.0,
}

PLAN_LABELS = {
    "monthly": "月度会员",
    "yearly": "年度会员",
}

PLAN_DAYS = {
    "monthly": 30,
    "yearly": 365,
}


# ============ Models ============

class CreatePaymentRequest(BaseModel):
    user_id: str
    plan: str  # "monthly" | "yearly"


class CheckPaymentResponse(BaseModel):
    order_id: str
    status: str  # "pending" | "paid"
    paid_type: Optional[str] = None


# ============ Helpers ============

def _generate_order_id() -> str:
    ts = int(time.time() * 1000)
    rand = uuid.uuid4().hex[:8]
    return f"ORD{ts}{rand}"


def _sign_params(params: dict) -> str:
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _verify_notify_hash(params: dict) -> bool:
    received_hash = params.get("hash", "")
    if not received_hash:
        return False
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return received_hash == expected


# ============ Routes ============

@router.post("/create")
async def create_payment(req: CreatePaymentRequest):
    """创建支付订单"""
    if req.plan not in PRICES:
        raise HTTPException(status_code=400, detail="无效的套餐类型")

    if is_paid(req.user_id):
        return {"message": "用户已付费", "already_paid": True}

    order_id = _generate_order_id()
    amount = PRICES[req.plan]
    plan_label = PLAN_LABELS[req.plan]

    create_order(order_id, req.user_id, amount, req.plan)

    nonce = str(int(time.time()))
    pay_params = {
        "version": "1.1",
        "appid": XUNHU_APPID,
        "trade_order_id": order_id,
        "total_fee": str(amount),
        "title": f"AI Auto Deploy - {plan_label}",
        "body": f"AI Auto Deploy {plan_label}，享生成项目与代码修复功能",
        "notify_url": "/api/payment/notify",
        "nonce_str": nonce,
        "time": nonce,
        "type": "WAP",
    }
    pay_params["hash"] = _sign_params(pay_params)

    try:
        resp = requests.post(
            f"{XUNHU_API}/payment/do.html",
            json=pay_params,
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise HTTPException(status_code=500, detail=f"支付创建失败: {data.get('errmsg', '未知错误')}")
        return {
            "order_id": order_id,
            "amount": amount,
            "plan": req.plan,
            "pay_url": data.get("url", ""),
            "already_paid": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"支付服务异常: {str(e)}")


@router.post("/notify")
async def payment_notify(request: Request):
    """虎皮椒支付回调"""
    form = await request.form()
    params = dict(form)

    if not _verify_notify_hash(params):
        raise HTTPException(status_code=400, detail="签名验证失败")

    order_id = params.get("trade_order_id", "")
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    update_order_status(order_id, "paid")

    user_id = order["user_id"]
    paid_type = order["paid_type"]
    now = datetime.now()

    days = PLAN_DAYS.get(paid_type, 30)
    expires = now + timedelta(days=days)
    upsert_user(user_id, paid_type, now.isoformat(), expires.isoformat())

    return {"errcode": 0, "errmsg": "success"}


@router.get("/check/{order_id}")
async def check_payment(order_id: str):
    """检查支付状态"""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_id": order_id,
        "status": order["status"],
        "paid_type": order.get("paid_type"),
        "amount": order["amount"],
    }


@router.get("/user/{user_id}")
async def get_user_payment(user_id: str):
    """查询用户付费状态"""
    user = get_user(user_id)
    paid = is_paid(user_id)

    return {
        "user_id": user_id,
        "paid": paid,
        "paid_type": user["paid_type"] if user else "free",
        "paid_at": user.get("paid_at") if user else None,
        "expires_at": user.get("expires_at") if user else None,
        "prices": PRICES,
        "plan_labels": PLAN_LABELS,
    }


@router.get("/prices")
async def get_prices():
    """获取价格信息"""
    return {
        "prices": PRICES,
        "plan_labels": PLAN_LABELS,
        "description": {
            "monthly": "月度会员 - 有效期 30 天",
            "yearly": "年度会员 - 有效期 365 天，省 522 元",
        },
    }
