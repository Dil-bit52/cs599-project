# Deployment Guide

This guide deploys ResearchPilot to a Docker server using Docker Compose.

Target server used for the course demo:

```text
Public IP: 60.205.203.170
Docker: 26.1.3
Frontend: http://60.205.203.170:3000
Backend API: http://60.205.203.170:8000
```

## 1. Open Server Ports

In the cloud console security group/firewall, allow inbound TCP ports:

```text
22    SSH
3000  ResearchPilot web
8000  ResearchPilot API
```

For a short course demo, exposing 3000 and 8000 is enough. For a production setup, put Nginx in front and only expose 80/443.

## 2. Upload Code

Option A: clone from GitHub after the repository has been pushed:

```bash
ssh root@60.205.203.170
mkdir -p /opt
cd /opt
git clone https://github.com/Dil-bit52/cs599-project.git
cd cs599-project
```

Option B: upload the prepared ZIP package from the local machine:

```powershell
scp "C:\Users\Administrator\Documents\New project\cs599-project.zip" root@60.205.203.170:/opt/
```

Then unzip it on the server:

```bash
ssh root@60.205.203.170
cd /opt
unzip cs599-project.zip -d cs599-project
cd cs599-project
```

## 3. Create `.env`

Create `/opt/cs599-project/.env` on the server:

```bash
cat > .env <<'EOF'
RESEARCHPILOT_APP_NAME=ResearchPilot API

RESEARCHPILOT_DATA_DIR=/app/data
RESEARCHPILOT_DB_PATH=/app/data/researchpilot.db
RESEARCHPILOT_REPORTS_DIR=/app/data/reports
RESEARCHPILOT_CACHE_DIR=/app/data/cache
RESEARCHPILOT_CHROMA_DIR=/app/data/chroma

CORS_ORIGINS=http://60.205.203.170:3000,http://localhost:3000,http://127.0.0.1:3000

LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=replace_with_your_real_api_key
OPENAI_COMPATIBLE_BASE_URL=https://token.sensenova.cn/v1
OPENAI_COMPATIBLE_MODEL=sensenova-6.7-flash-lite

LLM_TIMEOUT=45
LLM_TEMPERATURE=0.2
LLM_MAX_RETRIES=2

NEXT_PUBLIC_API_BASE_URL=http://60.205.203.170:8000
WEB_PORT=3000
API_PORT=8000
EOF
```

Replace `replace_with_your_real_api_key` with the real API key. Do not commit `.env` to Git.

## 4. Start Services

```bash
docker compose up -d --build
docker compose ps
```

Check backend health:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

Open the web UI:

```text
http://60.205.203.170:3000
```

## 5. Common Operations

View logs:

```bash
docker compose logs -f api
docker compose logs -f web
```

Restart:

```bash
docker compose restart
```

Rebuild after changing `.env` API address or frontend code:

```bash
docker compose down
docker compose build --no-cache web
docker compose up -d
```

Update from GitHub:

```bash
git pull
docker compose up -d --build
```

Stop:

```bash
docker compose down
```

## 6. Troubleshooting

If the page opens but task creation fails, check whether the browser can access:

```text
http://60.205.203.170:8000/api/health
```

If this URL is not reachable, check the cloud security group and server firewall.

If the frontend still requests `localhost:8000`, rebuild the frontend image with:

```bash
docker compose build --no-cache web
docker compose up -d
```

If the workflow fails at LLM nodes, check `.env` values and API logs:

```bash
docker compose logs -f api
```
