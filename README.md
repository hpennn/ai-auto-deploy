# 🚀 AI Auto Deploy

**智能一键部署工具** — 自动识别项目类型，生成部署脚本，一键部署到云服务器。

## ✨ 功能

- 🔍 **自动识别项目类型** — Python(FastAPI/Flask/Django)、Node.js(Next.js/Nuxt/Astro/React/Vue)、纯静态站点
- 📦 **自动选择包管理器** — npm/yarn/pnpm/bun/pip
- 🖥️ **多部署目标** — 云服务器SSH / Cloudflare Pages / Docker
- 🏗️ **自动生成配置** — Nginx配置、systemd服务、Dockerfile、docker-compose
- 🎛️ **宝塔面板支持** — 自动适配宝塔 Nginx 配置目录
- 💾 **配置持久化** — 服务器信息保存本地，下次部署直接用

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/hpennn/ai-auto-deploy.git
cd ai-auto-deploy

# 2. 首次运行（配置服务器）
python deploy.py

# 3. 后续部署
python deploy.py
# 按提示选择项目目录 → 自动检测 → 选择目标 → 生成脚本 → 部署
```

## 📋 支持的项目类型

| 类型 | 框架 | 部署方式 |
|------|------|---------|
| Python | FastAPI | PM2 + Uvicorn + Nginx |
| Python | Flask | PM2 + Gunicorn + Nginx |
| Python | Django | PM2 + Gunicorn + Nginx |
| Node.js | Next.js (SSR) | PM2 + Nginx |
| Node.js | Nuxt.js (SSR) | PM2 + Nginx |
| Node.js | Astro / Vite | 构建 → 静态文件 + Nginx |
| Node.js | React / Vue (SPA) | 构建 → 静态文件 + Nginx |
| 静态 | HTML | Nginx 直接服务 |
| Docker | 任意 | Dockerfile + docker-compose |

## 🎯 部署方式

### 方式一：云服务器（SSH）
自动登录服务器，安装依赖，启动服务，配置Nginx反向代理。

### 方式二：Cloudflare Pages
生成 wrangler.toml，一键部署到 Cloudflare 边缘网络。

### 方式三：Docker
生成 Dockerfile + docker-compose.yml，容器化部署。

## 🔧 命令

```bash
# 交互式部署（默认）
python deploy.py

# 配置服务器信息
python deploy.py config
```

## 📁 生成的文件

部署后会在项目目录生成：
- `deploy.sh` — 一键部署脚本（复制到服务器执行）
- `nginx.conf` — Nginx 反向代理配置
- `Dockerfile` — Docker 镜像构建（选Docker模式时）
- `docker-compose.yml` — 容器编排（选Docker模式时）

## 🛠️ 技术栈

- Python 3.8+
- 纯标准库，零外部依赖
- 支持 Ubuntu / CentOS / Debian

## 📝 示例

```
$ python deploy.py

╔══════════════════════════════════════╗
║       🚀 AI Auto Deploy v1.0        ║
║    智能识别 · 一键部署 · 多平台支持    ║
╚══════════════════════════════════════╝

📁 项目目录路径（默认当前目录）: /www/my-app

🔍 检测项目类型...
  📦 项目名: my-app
  🏗️  类型: python
  🔧 框架: fastapi
  📋 包管理: pip

🎯 选择部署目标：
  [0] 云服务器（SSH）
  [1] Cloudflare Pages
  [2] 生成本地部署脚本
  [3] 生成 Docker 部署
  选择 [0]: 0

✅ 部署脚本已生成: /www/my-app/deploy.sh
```

## License

MIT
