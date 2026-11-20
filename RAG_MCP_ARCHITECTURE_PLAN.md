# OpenBioMaps RAG & MCP Szerver Implementációs Terv

Ez a dokumentum részletes megvalósítási tervet nyújt az `OBM-RAG` projekthez, melynek célja az OpenBioMaps magyar nyelvű hivatalos dokumentációjára (`documentation/official_docs/hu`) épülő **RAG (Retrieval-Augmented Generation)** rendszer, egy szabványos **MCP (Model Context Protocol) szerver**, valamint az ezeket automatizáló **CI/CD pipeline és Docker image build** kialakítása.

---

## 1. Technológiai kérdések és döntések

### 1.1. Python `uv` mint csomag- és környezetkezelő
**Döntés: Igen, határozottan a `uv` az ideális eszköz.**
- **Rendkívüli sebesség:** Rust alapú, 10–100-szor gyorsabb, mint a hagyományos `pip`, `pip-tools` vagy `poetry`.
- **Projekt- és függőségkezelés:** Teljes körű `pyproject.toml` és cross-platform determinisztikus `uv.lock` támogatás.
- **Kiváló Docker integráció:** A `uv` beépített funkciókkal rendelkezik a Docker rétegek gyors és hatékony cache-eléséhez (`uv sync --frozen --no-install-project`, multi-stage build).
- **Beépített virtuális környezet és eszközfuttató:** Feleslegessé teszi az összetett pipenv/poetry/venv lépéseket (`uv run ...`, `uv tool ...`).
- **Gyors CI/CD:** GitHub Actions alatt az `astral-sh/setup-uv` akcióval és a beépített cache-sel másodpercek alatt kész a környezet.

### 1.2. Szükséges-e a Docling, és kell-e Pandoc a szövegkonverzióhoz?
**Döntés: Sem Docling, sem Pandoc NEM szükséges. Tiszta, natív Python feldolgozást használunk.**
- **Miért nem Docling?**
  - A Docling mélytanulási (vision/OCR) modellekre épül, amelyek célja szkennelt PDF-ek, elrendezés-alapú Word dokumentumok és képek beolvasása.
  - A mi forrásunk tiszta szövegállományokból áll (`.rst` és `.md`).
  - A Docling beemelése több gigabájttal növelné a Docker image méretét (PyTorch, modellek), miközben a szöveges RST formátumhoz semmilyen plusz értéket nem adna.
- **Miért nem Pandoc?**
  - A Pandoc egy külső C/Haskell alapú bináris rendszerfüggőség (`apt-get install pandoc`), ami feleslegesen bonyolítaná a konténert.
  - Pythonban natívan rendelkezésre áll a standard **`docutils`** (amire maga a Sphinx is épül), amivel tisztán Python kódból pár sorban kinyerhetők a fejezetek és a tiszta szöveg, felesleges külső binárisok nélkül.

### 1.3. Dokumentáció mérete és CPU-s vektorizálási sebesség (On-Premise / No GPU)
- **Tényleges adatmennyiség a repóban:**
  - A `documentation/official_docs/hu` mappa összesen **34 fájlból** áll (26 db `.rst` és 8 db `.md`).
  - Teljes sorok száma: **14 281 sor** (~70 000–90 000 szó, ~110 000 token).
  - Szemantikus fejezet-alapú szeleteléssel ebből mindössze **kb. 200–350 db chunk** (szövegrészlet) keletkezik.
- **CPU sebesség és futási idő:**
  - Standard 2–4 vCPU szerveren a vektorizálás sebessége modelltől függően: **5–25 chunk / másodperc**.
  - **A TELJES dokumentáció újraindexelése CPU-n mindössze 15–90 másodpercet vesz igénybe!** Nincs szükség GPU-ra az indexeléshez.

### 1.4. Modellválasztás: Melyik a legmegfelelőbb CPU-ra?
1. **BAAI / bge-m3 (Ajánlott prémium opció):**
   - Jelenlegi élvonalbeli modell, kiemelkedő magyar nyelvi megértéssel.
   - Sűrű (dense) és kulcsszó-alapú (sparse) keresést is támogat.
   - Méret: ~2.2 GB. CPU-s futási idő 300 chunkra: ~1–1.5 perc.
2. **intfloat / multilingual-e5-small vagy base (Ajánlott szupergyors/könnyű opció):**
   - Nagyon jó magyar nyelvi találati pontosság.
   - A `small` mérete mindössze ~470 MB, és 2-3-szor gyorsabb CPU-n, mint a BGE-M3 (mindössze ~15-20 másodperc a teljes dokumentáció).
3. **FastEmbed motor (ONNX Runtime):**
   - PyTorch helyett az ONNX Runtime-ot használja CPU-ra optimalizált kvantálással (INT8/FP32). Nem igényel 2 GB-os PyTorch csomagot a Dockerben, és 2-3x gyorsabb.

### 1.5. CI/CD és Erőforrások: GitHub Actions (Free Tier)
- **GitHub Free keret:** Havi **2 000 ingyenes Actions perc** (jóval bőségesebb, mint a GitLab 400 perce).
- **GitHub Runner:** 2 vCPU, 7 GB RAM, 14 GB SSD. Bőségesen elegendő a BGE-M3 modellhez és a Docker buildhez is.
- **Teljes CI/CD futásidő:** A kódellenőrzés + indexelés + Docker build összesen **kb. 2–3 perc**.
- **Kvótafelhasználás:** Havi 10 dokumentáció frissítés esetén mindössze ~25 percet használunk el a 2 000-ből (~1.25%).
- **Optimalizáció:**
  - `paths: ['documentation/official_docs/hu/**', 'src/**', 'Dockerfile']` szűrővel csak akkor indul el a build, ha a dokumentáció vagy a kód valóban módosult.
  - A letöltött modellek cache-elése GitHub Actions cache-sel, így nem kell minden buildnél újra letölteni az internetről.

### 1.6. Repository architektúra: Almappa vs. Külön Repo
- **A) Fejlesztési fázisban (Most):** Almappás / lokális struktúra az aktuális `OBM-RAG` könyvtáron belül a legkényelmesebb a teszteléshez és az indexelő finomhangolásához.
- **B) Éles/Végleges állapotban:** 
  - Külön repo (pl. `openbiomaps/obm-rag` vagy `obm-rag-mcp`) ajánlott.
  - A dokumentációs repo megmarad tiszta dokumentációként, a RAG repo pedig:
    - vagy **Git submodule**-ként hivatkozik a dokumentációra,
    - vagy a GitHub Actions workflow checkout lépésben közvetlenül lehúzza a dokumentációs repo `main` ágát a Docker build előtt.

---

## 2. Rendszerarchitektúra és komponensek

### 2.1. Adatforrás
- **Helye:** `documentation/official_docs/hu/`
- **Típusok:** Sphinx reStructuredText (`.rst`), Markdown (`.md`) fájlok.
- **Feldolgozási cél:** A címsorok hierarchiájának, fejezeteknek és kódblokkoknak a megőrzése, és metaadatok (forrásfájl, fejezetcím, szekció) hozzárendelése a chunk-okhoz.

### 2.2. Ingestion & RAG Pipeline (Natív megközelítés)
- **Parser & Loader (natív Python):** 
  - **`.rst` fájlok:** A Python standard **`docutils`** parserével a szöveg fejezeteit bejárjuk. Kiszűri a Sphinx-specifikus vezérlőket (`:doc:`, `.. TODO:`, `.. note::`), de egyben tartja a logikai fejezeteket és a tiszta szöveget.
  - **`.md` fájlok:** Fejlécalapú felosztás (`#`, `##`, `###` mentén), megőrizve a fejezethierarchiát.
- **Chunking stratégia:**
  - Szemantikus fejezet-alapú tördelés (Header-based chunking), max. 500–800 token chunk mérettel és 100 token átfedéssel, ha egy fejezet túl hosszú.
- **Embedding & Vektoradatbázis (Vector Store):**
  - **Motor:** **FastEmbed** (`BAAI/bge-m3` vagy `intfloat/multilingual-e5-small`).
  - **Adatbázis:** **ChromaDB** vagy **LanceDB** (beágyazott, szerver nélküli, fájlrendszeren perzisztálható a `data/vector_store/` könyvtárban).
  - **Együttes betöltés:** A `build_index.py` a memóriában előállított chunkokhoz kiszámolja az embeddingeket, és a szöveget, metaadatokat és vektorokat egyszerre menti el a lemezre.

### 2.3. MCP (Model Context Protocol) Szerver
- **Protokoll:** Hivatalos Python MCP SDK (`mcp`).
- **Architektúra elv:** Az MCP szerver **tiszta Retrieval szolgáltatás** (Search & Context Provider). Nem tartalmaz belső LLM válaszgenerátort (`generator.py`), mert a választ a hívó LLM kliens (VS Code Copilot, Claude Desktop stb.) állítja össze a kapott pontos kontextusból. Ez kiküszöböli a kettős késleltetést, a felesleges token-költségeket és az információvesztést.
- **Kommunikációs mód:**
  - **STDIO** (helyi futtatáshoz VS Code, Claude Desktop, Cursor kliensekhez).
  - **SSE / HTTP Streamable** (távoli konténeres eléréshez, mikroszolgáltatásként).
- **MCP Eszközök (Tools):**
  1. `rag_search(query: str, limit: int = 5)`: Szemantikus és kulcsszó-alapú keresés a magyar dokumentációban; visszatér a leginkább releváns szövegrészletekkel (chunkok), metaadatokkal (fájl, fejezetcím) és pontszámokkal a kliens LLM számára.
  2. `read_documentation_page(path: str)`: Teljes dokumentációs oldal lekérése az eredeti formátumban (ha a modellnek egy teljes fájl kontextusára van szüksége).
- **MCP Erőforrások (Resources):**
  - `obm://docs/toc`: A hivatalos magyar dokumentáció tartalomjegyzéke.
  - `obm://docs/{page_name}`: Adott oldal közvetlen szöveges elérése.

---

## 3. Ajánlott mappastruktúra

```
OBM-RAG/
├── .github/
│   └── workflows/
│       ├── test.yml            # CI: kódminőség, típusok, tesztek
│       └── build-image.yml     # CD: RAG index frissítés, Docker build & push
├── documentation/
│   ├── official_docs/
│   │   └── hu/                 # A forrás dokumentáció
│   └── ...
├── src/
│   └── obm_rag/
│       ├── __init__.py
│       ├── config.py           # Környezeti változók, beállítások
│       ├── ingestion/          # Dokumentáció feldolgozás & indexelés
│       │   ├── __init__.py
│       │   ├── rst_parser.py   # RST és MD felolvasó, chunker
│       │   └── indexer.py      # Vektorizálás és DB feltöltés
│       ├── rag/                # Lekérdezési és retriever logika
│       │   ├── __init__.py
│       │   └── retriever.py    # Vektoros és szemantikus kereső
│       └── mcp/                # MCP szerver implementáció
│           ├── __init__.py
│           ├── server.py       # MCP Server definíció és futtatás
│           └── tools.py        # Keresési és lekérdező eszközök
├── scripts/
│   ├── build_index.py          # Parancssori script az index újraépítéséhez
│   └── test_query.py           # Manuális tesztelő script
├── data/
│   └── vector_store/           # Generált vektorindex (lokális cache / pre-built)
├── tests/
│   ├── test_parser.py
│   ├── test_retriever.py
│   └── test_mcp_tools.py
├── .dockerignore
├── .gitignore
├── Dockerfile                  # Multi-stage Dockerfile uv-val
├── pyproject.toml              # Projekt leírás és uv függőségek
└── uv.lock                     # Determinisztikus függőségfa
```

---

## 4. `pyproject.toml` és függőségek (uv minta)

```toml
[project]
name = "obm-rag"
version = "0.1.0"
description = "OpenBioMaps Documentation RAG and MCP Server"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.2.0",
    "docutils>=0.21.0",
    "chromadb>=0.5.0",
    "fastembed>=0.3.0",        # CPU-ra optimalizált ONNX embedding (BGE-M3 vagy E5)
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "rich>=13.7.0",
]

[project.scripts]
obm-mcp = "obm_rag.mcp.server:main"
obm-index = "scripts.build_index:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.4.0",
]
```

---

## 5. Dockerfile tervezés (`uv` multi-stage build)

A Docker image-be beépíthető az előre legyártott vektorindex, így az image azonnal kiszolgálásra kész és nem igényel indulási indexelést:

```dockerfile
# 1. Builder réteg: uv és függőségek telepítése
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# UV beállítások a gyors és determinisztikus buildhez
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Függőségek telepítése lockfile alapján
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Forráskód és dokumentáció másolása
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY documentation/ ./documentation/
COPY README.md ./

# Projekt telepítése
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Dokumentáció indexelése a build során (beépített index)
# Megjegyzés: Ha API kulcs szükséges az embeddinghez, az build-secretként átadható
RUN uv run python -m scripts.build_index --docs-path documentation/official_docs/hu --output-dir /app/data/vector_store

# 2. Végleges futtató réteg
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Másoljuk át a virtuális környezetet, kódot és az előre elkészített indexet
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/data/vector_store /app/data/vector_store

EXPOSE 8000

# Alapértelmezett indítás (MCP szerver STDIO vagy SSE módban)
ENTRYPOINT ["obm-mcp"]
```

---

## 6. CI/CD folyamat tervezése (GitHub Actions)

Két fő munkafolyamat (workflow) ajánlott:

### 6.1. `CI: Kód- és dokumentáció-ellenőrzés (.github/workflows/test.yml)`
- **Trigger:** Pull request vagy push bármelyik ágra.
- **Feladatok:**
  1. `uv` környezet beállítása (`astral-sh/setup-uv@v3`).
  2. Kódformázás és linter futtatása (`uv run ruff check .`).
  3. Egységtesztek futtatása (`uv run pytest`).
  4. Próba-indexelés validálása (dry-run a docs/hu fájlokon).

### 6.2. `CD: RAG Indexelés & Docker Image Build (.github/workflows/build-image.yml)`
- **Trigger:**
  - Push a `main` ágra, ha a `documentation/official_docs/hu/**` vagy az alkalmazáskód módosul (`paths:` szűrővel).
  - Kézi indítás (`workflow_dispatch`).
- **Lépések:**
  1. Kód letöltése (`actions/checkout`).
  2. Docker Buildx beállítása.
  3. Bejelentkezés GitHub Container Registry-be (GHCR: `ghcr.io/${{ github.repository }}/obm-rag-mcp`).
  4. Actions Cache beállítása a letöltött FastEmbed/HuggingFace modellekhez (gyorsítja a buildet).
  5. Multi-stage Docker build futtatása:
     - Leindexeli a dokumentációt.
     - Becsomagolja a perzisztens indexet és az MCP szervert.
     - Push-olja a kész konténert `latest` és git sha címkékkel.

---

## 7. Részletes Megvalósítási Lépések (Roadmap)

### 1. Fázis: Projekt Inicializálás és Ingestion Fejlesztése
- [ ] `pyproject.toml` létrehozása és `uv` init (`uv init --app`).
- [ ] RST/MD parser megírása (`rst_parser.py`):
  - Kifejezetten a Sphinx RST szerkezetek (címsorok, direktívák, kódrészletek) tisztítása és szekcionálása.
  - Metaadatok kinyerése: fájl elérési útja, dokumentum címe, fejezet címe.
- [ ] Indexelő script (`build_index.py`) elkészítése:
  - Dokumentumok beolvasása `documentation/official_docs/hu` könyvtárból.
  - Chunking, embedding generálás és perzisztálás ChromaDB / LanceDB tárolóba.

### 2. Fázis: Kereső és MCP Szerver Kialakítása
- [ ] Vektoros retriever modul elkészítése (`retriever.py`):
  - Hasonlósági keresés (top-k szekció kinyerése relevanciával).
- [ ] MCP szerver implementálása (`mcp/server.py`):
  - FastMCP vagy Standard MCP szerver inicializálása.
  - `search_docs` és `get_doc_page` tool-ok regisztrálása.
  - Helyi tesztelés `uv run obm-mcp` futtatásával (pl. MCP Inspectorral vagy VS Code / Claude Desktop konfigurációval).

### 3. Fázis: Konténerizálás és Dockerfile
- [ ] Dockerfile megírása (multi-stage build `uv`-val).
- [ ] `.dockerignore` konfigurálása.
- [ ] Helyi Docker build és futtatási teszt ellenőrzése.

### 4. Fázis: CI/CD Pipeline Felépítése
- [ ] `.github/workflows/build-image.yml` elkészítése.
- [ ] GHCR (GitHub Packages) jogosultságok beállítása a repository-ban.
- [ ] Automatikus triggerelés tesztelése a dokumentáció egy teszt commitjával.
