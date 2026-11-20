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
uv run obm-mcp
```
