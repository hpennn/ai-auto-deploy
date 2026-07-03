"""
AI Auto Deploy - Web Backend
FastAPI application entry point
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so we can import src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from web.api.deploy import router as deploy_router
from web.api.servers import router as servers_router
from web.api.fix import router as fix_router
from web.api.generate import router as generate_router
from web.api.payment import router as payment_router
from web.api.admin import router as admin_router

app = FastAPI(
    title="AI Auto Deploy",
    description="智能一键部署工具 - Web API",
    version="1.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(deploy_router, prefix="/api/deploy", tags=["deploy"])
app.include_router(servers_router, prefix="/api/servers", tags=["servers"])
app.include_router(fix_router, prefix="/api/fix", tags=["fix"])
app.include_router(generate_router, prefix="/api/generate", tags=["generate"])
app.include_router(payment_router, prefix="/api/payment", tags=["payment"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "AI Auto Deploy API", "version": "1.2.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
