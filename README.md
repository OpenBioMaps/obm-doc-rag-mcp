# OpenBioMaps RAG & MCP Szerver

Hivatalos OpenBioMaps magyar dokumentációra épülő publikus szemantikus kereső és [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) szerver.

A projekt célja, hogy központi, publikusan elérhető MCP szerverként szolgálja ki az AI klienseket (VS Code GitHub Copilot, Cursor, Claude, webes AI asszisztensek stb.). A felhasználóknak a saját gépükre semmit sem kell telepíteniük: csupán a szerver URL-jét kell megadniuk az AI eszközükben.

A dokumentációt a rendszer a Docker build során automatikusan beindexeli (ChromaDB vektortár + FastEmbed modell), és azonnal futtatható konténerként teszi közzé a GitHub Container Registry-ben (GHCR).

---

## 🌐 Publikus Szerver Végpontok

A szerver az alábbi szabványos MCP protokollokat támogatja:

| Protokoll | Végpont URL | Leírás |
| :--- | :--- | :--- |
| **Streamable HTTP** *(Ajánlott, alapértelmezett)* | `http(s)://<SZERVER_IP_VAGY_DOMAIN>:8000/mcp` | A legújabb, modern MCP HTTP szabvány. Közvetlenül használható webes és asztali kliensekből. |
| **Server-Sent Events (SSE)** | `http(s)://<SZERVER_IP_VAGY_DOMAIN>:8000/sse` | Hagyományos SSE transzport régebbi kliensekhez. |

---

## 🚀 Szerver Telepítés és Üzemeltetés (Docker Compose)

A szerverre **nem kell letölteni vagy klónozni a forráskódot**. A futtatáshoz mindössze a `docker-compose.yml` fájl szükséges, amely közvetlenül a GitHub Container Registry-ből (`ghcr.io`) húzza le a készre indexelt konténert.

### 1. Telepítés és indítás (1 perc)

```bash
# 1. Mappa létrehozása a szerveren és belépés
mkdir -p /srv/docker/obm-rag
cd /srv/docker/obm-rag

# 2. docker-compose.yml letöltése a GitHubról
curl -O https://raw.githubusercontent.com/<SZERVEZET_VAGY_USER>/<REPO_NEV>/master/docker-compose.yml

# 3. (Opcionális) Környezeti beállítások testreszabása
# cat << 'EOF' > .env
# PORT=8000
# OBM_TRANSPORT=streamable-http
# EOF

# 4. Image letöltése és konténer indítása a háttérben
docker compose pull
docker compose up -d
```

### 2. HTTPS és Reverse Proxy beállítása (Nginx minta)

Éles publikus üzemhez ajánlott domain név és SSL tanúsítvány (pl. Let's Encrypt) használata:

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
        
        # Streamable HTTP és SSE streaming beállítások
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### 3. Frissítés új verzióra

Amikor a GitHub Actions elkészíti az új image-et, a szerveren csupán ezt a parancsot kell kiadni a frissítéshez:

```bash
docker compose pull && docker compose up -d
```

---

## 💻 Kliens Csatlakozás a Publikus Szerverhez

A végfelhasználóknak **nincs szükségük Dockerre, Pythonra vagy helyi forráskódra**. Csupán a szerver URL-jét kell konfigurálniuk a preferált fejlesztői vagy AI eszközükben:

### 1. VS Code GitHub Copilot beállítása

A felhasználó a projektjének `.vscode/mcp.json` fájljába (vagy globális felhasználói beállításaiba) az alábbi bejegyzést illeszti be:

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

*(Ha a szervert még IP címen éritek el reverse proxy nélkül: `"url": "http://<SZERVER_IP>:8000/mcp"`)*

Ezt követően a Copilot Chat automatikusan meghívja az OpenBioMaps keresőt (`rag_search`), ha a felhasználó a működésről, rétegekről, konfigurációról kérdez.

---

### 2. Cursor IDE beállítása

A Cursor **Settings -> Features -> MCP** felületén:
1. Kattints az **Add new MCP server** gombra.
2. Név: `OpenBioMaps Docs`
3. Típus: `HTTP` (vagy `SSE`)
4. URL: `https://mcp.openbiomaps.org/mcp`

---

### 3. Claude Desktop / egyéb távoli MCP kliensek

A távoli HTTP/SSE végpont támogatásával rendelkező kliensekben elegendő a megosztott `https://mcp.openbiomaps.org/mcp` URL megadása.

---

## 🔄 CI/CD és Dokumentáció Változáskövetés (GitHub Actions)

A repóban lévő munkafolyamatok teljesen automatizálják az életciklust:

1. **`ci.yml`**: Minden commit és PR esetén ellenőrzi a kódot (Ruff) és lefuttatja a Pytest egységteszteket.
2. **`build-and-publish.yml`**:
   - Letölti a hivatalos [OpenBioMaps/documentation](https://github.com/OpenBioMaps/documentation) repó tartalmát.
   - Elvégzi a dokumentumok felosztását és beindexeli őket a Docker build fázisban (`pre-baked index`).
   - Publikálja az új verziót a GitHub Container Registry-be: `ghcr.io/<szervezet_vagy_user>/<repo_nev>:latest`.

### Dokumentáció automatikus frissítése Webhookkal (`repository_dispatch`)

Ahhoz, hogy az [OpenBioMaps/documentation](https://github.com/OpenBioMaps/documentation) repó módosulásakor a szerver image azonnal és automatikusan újraépüljön, helyezd el az alábbi workflow-t a dokumentációs repó `.github/workflows/notify-rag.yml` fájljában:

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
          repository: <SZERVEZET_VAGY_USER>/<RAG_REPO_NEV>
          event-type: documentation_updated
```

---

## 🧰 Elérhető MCP Eszközök (Tools)

- **`rag_search(query: str, limit: int = 5)`**: Szemantikus keresés az OpenBioMaps hivatalos magyar dokumentációjában. Visszaadja a leginkább releváns szövegrészleteket, azok témáját, fejezethierarchiáját, a forrásfájl elérési útját és a relevancia pontszámot.
- **`read_documentation_page(path: str)`**: Egy teljes dokumentációs oldal beolvasása az eredeti formájában (`.rst` vagy `.md`), path-traversal védelemmel.
- **`list_documentation_pages()`**: A magyar dokumentációban elérhető oldalak listája a teljes dokumentációs fa áttekintéséhez.
