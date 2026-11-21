# OpenBioMaps RAG & MCP Szerver

Hivatalos OpenBioMaps magyar dokumentációra épülő szemantikus kereső és Model Context Protocol (MCP) szerver.

## Használat

### Függőségek telepítése (uv segítségével)
```bash
uv sync
```

### Index építése
```bash
uv run python -m scripts.build_index --docs-path documentation/official_docs/hu
```

### Keresés tesztelése parancssorból
```bash
uv run python -m scripts.test_query "Hogyan kell réteget importálni?"
```

### MCP szerver futtatása
```bash
# STDIO mód (helyi AI kliensekhez)
uv run obm-mcp

# SSE / HTTP mikroszolgáltatás mód
uv run obm-mcp --transport sse --port 8000
```

## Integráció MCP Kliensekkel

### 1. VS Code GitHub Copilot beállítása

A VS Code Copilot támogatja az MCP szervereket a workspace szintű `.vscode/mcp.json` konfigurációs fájlon keresztül vagy a felhasználói beállításokban.

#### A) Workspace-szintű beállítás (`.vscode/mcp.json`):
A VS Code natív `servers` sémát használ `"type": "stdio"` megjelöléssel:

```json
{
  "servers": {
    "openbiomaps-rag": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "obm_rag.mcp.server"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```
>       ]
>     }
>   }
> }
> ```

#### B) Használat a VS Code Copilot Chatben:
1. Nyisd meg a Copilot Chat ablakot (`Ctrl + Alt + I` vagy a bal oldali sáv).
2. A Chat automatikusan felismeri az `OpenBioMaps-Documentation-RAG` szerver által regisztrált eszközöket.
3. Bármilyen OpenBioMaps-re vonatkozó kérdés esetén a Copilot magától meghívja a `rag_search` eszközt:
   - *"Hogyan kell réteget létrehozni az OpenBioMaps-ben?"*
   - *"Milyen paramétereket fogad a modules adminisztráció?"*
   - *"Hogyan telepíthetem a rendszert Dockerben?"*
4. A Copilot automatikusan beolvassa a pontos dokumentációs forrásrészleteket, és pontos hivatkozásokkal ellátott magyar választ állít össze.

---

### 2. Claude Desktop beállítása

A Claude Desktop beállítási fájljába (`%APPDATA%\Claude\claude_desktop_config.json` Windows alatt):

```json
{
  "mcpServers": {
    "openbiomaps-rag": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\GA\\_OBM\\CODE\\OBM-RAG",
        "run",
        "obm-mcp"
      ]
    }
  }
}
```

## Futtatás Dockerben

A Docker image a build során előre beindexeli a hivatalos magyar dokumentációt (`pre-baked index`), így azonnal kiszolgálásra kész további indexelés nélkül.

### Docker image építése helyileg
```bash
docker build -t obm-rag:latest .
```

### Futtatás konténerből

#### A) STDIO MCP mód (AI kliens konténeres indítása):
```bash
docker run -i --rm obm-rag:latest
```

#### B) SSE / HTTP mikroszolgáltatás mód:
```bash
docker run -d --name obm-rag -p 8000:8000 obm-rag:latest obm-mcp --transport sse --host 0.0.0.0 --port 8000
```

## CI/CD Folyamatok (GitHub Actions)

A `.github/workflows/` könyvtár két automatizált munkafolyamatot tartalmaz:
- **`ci.yml`**: Minden push és PR esetén futtatja a Ruff lintert és a 14 Pytest egységtesztet.
- **`build-and-publish.yml`**: Push a `main` ágra (vagy kézi indítás esetén) automatikusan felépíti a Docker image-et az előre generált indexszel, és közzéteszi a GitHub Container Registry-ben (`ghcr.io/<owner>/obm-rag:latest`).

## Elérhető MCP Eszközök (Tools)

- **`rag_search(query: str, limit: int = 5)`**: Szemantikus keresés az OpenBioMaps magyar dokumentációjában. Visszaadja a releváns szövegrészleteket, azok témáját, fejezethierarchiáját, a forrásfájl elérési útját és relevancia pontszámát.
- **`read_documentation_page(path: str)`**: Egy teljes dokumentációs oldal beolvasása az eredeti formájában (`.rst` vagy `.md`), path-traversal védelemmel.
- **`list_documentation_pages()`**: A magyar dokumentációban elérhető oldalak listája.

## Tesztek futtatása
```bash
uv run pytest
```
