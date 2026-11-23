# OpenBioMaps RAG & MCP Server

Semantic search and public [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server built on the official OpenBioMaps documentation.

The goal of this project is to provide a central, publicly accessible MCP server for AI clients (VS Code GitHub Copilot, Cursor, Claude, web-based AI assistants, etc.). End users do not need to install anything locally (no Python, no Docker): they only need to specify the server URL in their AI tools.

Documentation is automatically indexed during the Docker build stage (ChromaDB vector store + FastEmbed multilingual model) and published as a ready-to-run container on the GitHub Container Registry (GHCR).

---

## 🌐 Public Server Endpoints

The server supports standard MCP transports:

| Transport | Endpoint URL | Description |
| :--- | :--- | :--- |
| **Streamable HTTP** *(Recommended, default)* | `http(s)://<SERVER_IP_OR_DOMAIN>:8000/mcp` | Latest modern MCP HTTP standard. Usable directly by web and desktop clients. |
| **Server-Sent Events (SSE)** | `http(s)://<SERVER_IP_OR_DOMAIN>:8000/sse` | Traditional SSE transport for legacy clients. |

---

## 🚀 Server Deployment and Operation (Docker Compose)

There is **no need to clone or store source code on the production server**. Running the service only requires the `docker-compose.yml` file, which pulls the pre-built, pre-indexed container image directly from GitHub Container Registry (`ghcr.io`).

### 1. Installation and Startup (1 minute)

```bash
# 1. Create deployment directory and navigate to it
mkdir -p /srv/docker/obm-rag
cd /srv/docker/obm-rag

# 2. Download docker-compose.yml from GitHub
curl -O https://raw.githubusercontent.com/<OWNER>/<REPO>/master/docker-compose.yml

# 3. (Optional) Customize environment variables
# cat << 'EOF' > .env
# PORT=8000
# OBM_TRANSPORT=streamable-http
# EOF

# 4. Pull pre-built image and start in background
docker compose pull
docker compose up -d
```

### 2. HTTPS and Reverse Proxy Setup (Nginx example)

For production public deployments, a domain name and TLS certificate (e.g., Let's Encrypt) are recommended:

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.openbiomaps.org;

    ssl_certificate /etc/letsencrypt/live/mcp.openbiomaps.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.openbiomaps.org/privkey.pem;

    location /mcp {
        proxy_pass http://127.0.0.1:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streamable HTTP and SSE streaming configuration
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### 3. Updating to Latest Version

When a new image is published by GitHub Actions, update the server with a single command:

```bash
docker compose pull && docker compose up -d
```

---

## 💻 Client Integration with the Public Server

End users **do not need Docker, Python, or local source code**. They only need to configure the server URL in their preferred AI environment:

### 1. VS Code GitHub Copilot Setup

Add the server to your project's `.vscode/mcp.json` file (or user settings):

```json
{
  "servers": {
    "openbiomaps-rag": {
      "type": "http",
      "url": "https://mcp.openbiomaps.org/mcp"
    }
  }
}
```

*(If connecting via IP without a reverse proxy: `"url": "http://<SERVER_IP>:8000/mcp"`)*

Copilot Chat will automatically invoke the OpenBioMaps tool (`rag_search`) whenever answering questions about OpenBioMaps architecture, modules, layers, or configuration.

---

### 2. Cursor IDE Setup

In Cursor under **Settings -> Features -> MCP**:
1. Click **Add new MCP server**.
2. Name: `OpenBioMaps Docs`
3. Type: `HTTP` (or `SSE`)
4. URL: `https://mcp.openbiomaps.org/mcp`

---

### 3. Claude Desktop / Other Remote MCP Clients

For clients supporting remote HTTP/SSE endpoints, supply the shared `https://mcp.openbiomaps.org/mcp` URL in the MCP configuration.

---

## 🔄 CI/CD & Documentation Tracking (GitHub Actions)

Workflows included in this repository:

1. **`ci.yml`**: Runs code quality checks (Ruff linter) and executes unit tests (Pytest) on commits and pull requests.
2. **`build-and-publish.yml`**:
   - Clones official documentation from [OpenBioMaps/documentation](https://github.com/OpenBioMaps/documentation).
   - Chunks and indexes the documentation during Docker build (`pre-baked index`).
   - Publishes ready-to-run images to GitHub Container Registry: `ghcr.io/<owner>/<repo>:latest`.

### Automatic Rebuild via Documentation Webhook (`repository_dispatch`)

To automatically rebuild the Docker image whenever documentation changes in [OpenBioMaps/documentation](https://github.com/OpenBioMaps/documentation), add this workflow to the documentation repository (`.github/workflows/notify-rag.yml`):

```yaml
name: Notify RAG on Docs Update

on:
  push:
    branches: ["master", "main"]

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger RAG Image Rebuild
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.RAG_TRIGGER_PAT }}  # GitHub Personal Access Token (repo scope)
          repository: <OWNER>/<RAG_REPO_NAME>
          event-type: documentation_updated
```

---

## 🧰 Available MCP Tools

- **`rag_search(query: str, limit: int = 5)`**: Semantic search in OpenBioMaps documentation. Returns relevant snippets, topic hierarchy, source file paths, and relevance scores.
- **`read_documentation_page(path: str)`**: Reads a complete documentation page in raw format (`.rst` or `.md`) with path traversal protection.
- **`list_documentation_pages()`**: Lists all available documentation pages for hierarchy exploration.
