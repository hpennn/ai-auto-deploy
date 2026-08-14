FROM python:3.11-slim

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Install Python dependencies
COPY web/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy backend code
COPY web/ ./web/
COPY src/ ./src/
COPY deploy.py pyproject.toml README.md ./

# Copy pre-built frontend (already built in repo)
COPY frontend/dist ./frontend/dist

# Copy public assets
COPY public/ ./public/

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Switch to non-root user
USER root

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
