# 🚀 AI Auto Deploy

智能一键部署工具 - 自动识别项目类型，一键生成部署脚本。

## ✨ 功能

- 🔍 **智能检测** - 自动识别项目类型（Python/Node.js/静态站点）
- 🏗️ **框架识别** - 支持 FastAPI/Flask/Django/Next.js/Vue/React/Astro 等
- 📝 **脚本生成** - 自动生成部署脚本和 Nginx 配置
- 🐳 **Docker** - 一键生成 Dockerfile 和 docker-compose
- ☁️ **多平台** - 支持云服务器/Cloudflare Pages/本地部署
- 🌐 **Web UI** - 现代化深色主题界面

## 📦 快速开始

### CLI 模式

```bash
python deploy.py
```

### Web 模式

**后端：**

```bash
cd web
pip install -r requirements.txt
uvicorn main:app --reload
```

后端运行在 http://localhost:8000

**前端：**

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:3000

**前端构建：**

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/` 目录。

## 🛠️ 技术栈

### 后端
- Python 3.8+
- FastAPI
- Uvicorn

### 前端
- Vue 3
- Vite
- Element Plus

## 📁 项目结构

```
ai-auto-deploy/
├── deploy.py           # CLI 入口
├── src/
│   └── cli.py          # 核心逻辑（检测/生成/部署）
├── web/                # Web 后端
│   ├── main.py         # FastAPI 入口
│   └── api/
│       ├── deploy.py   # 部署 API
│       └── servers.py  # 服务器管理 API
└── frontend/           # Web 前端
    ├── src/
    │   ├── main.js
    │   ├── App.vue
    │   └── style.css
    └── package.json
```

## 🌐 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/deploy/detect` | 检测项目类型 |
| POST | `/api/deploy/generate` | 生成部署脚本 |
| POST | `/api/deploy/execute` | 执行部署 |
| GET  | `/api/servers` | 获取服务器列表 |
| POST | `/api/servers` | 添加服务器 |
| DELETE | `/api/servers/{index}` | 删除服务器 |

## 📄 License

MIT
