# OpenBioMaps RAG & MCP Server Architecture & Implementation Plan

This document outlines the architecture and implementation design for the `OBM-RAG` project, providing a **Retrieval-Augmented Generation (RAG)** system and a standard **Model Context Protocol (MCP) server** over the official OpenBioMaps documentation (`documentation/official_docs/hu`), supported by automated **CI/CD pipelines and Docker container packaging**.

---

## 1. Technical Decisions & Trade-offs

### 1.1. Python `uv` as Package & Environment Manager
**Decision: Yes, `uv` is the primary tool.**
- **Extreme performance:** Rust-based, 10–100x faster than legacy `pip`, `pip-tools`, or `poetry`.
- **Project & dependency management:** Native `pyproject.toml` support and cross-platform deterministic `uv.lock`.
- **Optimized Docker integration:** Built-in multi-stage caching features (`uv sync --frozen --no-install-project`).
- **Unified toolchain:** Eliminates cumbersome virtualenv management (`uv run ...`, `uv tool ...`).
- **Fast CI/CD:** Ready within seconds on GitHub Actions via `astral-sh/setup-uv` and action cache.

### 1.2. Docling vs. Pandoc vs. Native Python Parsing
**Decision: Neither Docling nor Pandoc is required. We use pure native Python parsing.**
- **Why not Docling?**
  - Docling focuses on OCR and layout-based conversion for scanned PDFs and complex Word files.
  - Our documentation consists of clean, structured text files (`.rst` and `.md`).
  - Including Docling would add gigabytes of PyTorch and vision model dependencies without adding value for plain RST.
- **Why not Pandoc?**
  - Pandoc requires external C/Haskell system binaries (`apt-get install pandoc`), complicating the container.
  - Python natively includes standard **`docutils`** (the foundation of Sphinx), allowing direct, clean extraction of section hierarchy and text.

### 1.3. Documentation Volume & CPU Vectorization Throughput (No GPU Needed)
- **Data volume in repository:**
  - `documentation/official_docs/hu` contains **34 files** (26 `.rst` and 8 `.md`).
  - Total line count: **~14,281 lines** (~70,000–90,000 words, ~110,000 tokens).
  - Semantic section-based chunking yields **~200–350 chunks**.
- **CPU throughput & execution time:**
  - Standard 2–4 vCPU server achieves **5–25 chunks / second**.
  - **Full re-indexing takes only 15–90 seconds on CPU.** No GPU is necessary.

### 1.4. Model Selection for CPU Execution
1. **FastEmbed runtime (ONNX Runtime):**
   - Utilizes ONNX Runtime with CPU-optimized INT8/FP32 execution instead of heavy PyTorch packages.
2. **sentence-transformers / paraphrase-multilingual-MiniLM-L12-v2:**
   - Lightweight, highly accurate across languages (including Hungarian), fast inference on CPU.

### 1.5. CI/CD & Free Tier Resources: GitHub Actions
- **GitHub Free Tier:** 2,000 free runner minutes per month.
- **GitHub Runner:** 2 vCPU, 7 GB RAM, 14 GB SSD. Fully sufficient for indexing and Docker builds.
- **Full CI/CD runtime:** Linting + testing + indexing + Docker build takes **~2–3 minutes**.

### 1.6. Repository Architecture
- **Documentation repository:** Clean source documentation in `OpenBioMaps/documentation`.
- **RAG & MCP repository:** Codebase for indexing, retriever, and MCP server.
- **CI/CD integration:** GitHub Actions checks out the documentation repository before building the Docker image.

---

## 2. System Architecture & Components

### 2.1. Data Source
- **Location:** `documentation/official_docs/hu/`
- **File types:** Sphinx reStructuredText (`.rst`), Markdown (`.md`).
- **Goal:** Preserve heading hierarchy, section context, and code blocks while attaching rich metadata (source path, document title, section breadcrumbs).

### 2.2. Ingestion & RAG Pipeline
- **Parser & Loader (native Python):**
  - **`.rst` files:** Custom parser built on `docutils`. Cleans Sphinx directives (`:doc:`, `.. note::`, `.. toctree::`) while keeping sections intact.
  - **`.md` files:** Heading-based splitter (`#`, `##`, `###`) maintaining document breadcrumbs.
- **Chunking strategy:**
  - Semantic section-based splitting, max 500–800 tokens per chunk with 80–100 token overlap for oversized sections.
- **Vector Store:**
  - **Engine:** **FastEmbed** (`paraphrase-multilingual-MiniLM-L12-v2`).
  - **Database:** **ChromaDB** (embedded, persistent filesystem storage in `data/vector_store/`).

### 2.3. MCP (Model Context Protocol) Server
- **Protocol:** Official Python MCP SDK (`mcp.server.mcpserver`).
- **Architectural role:** **Pure Retrieval & Context Provider**. The server does not invoke an internal generator LLM; the calling client LLM (Copilot, Claude, Cursor) synthesizes answers from retrieved context.
- **Transports:**
  - **Streamable HTTP** (`/mcp`): Recommended modern public standard for remote clients.
  - **SSE** (`/sse`): Traditional Server-Sent Events transport.
  - **STDIO**: Local command-line execution for local IDEs.
- **MCP Tools:**
  1. `rag_search(query: str, limit: int = 5)`: Semantic search returning relevant chunks, breadcrumbs, source paths, and relevance scores.
  2. `read_documentation_page(path: str)`: Safely reads the full content of any documentation file.
  3. `list_documentation_pages()`: Lists available documentation pages.
- **MCP Resources:**
  - `obm://docs/pages`: Direct resource access to the available documentation index.

---

## 3. Directory Structure

```
OBM-RAG/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Linting & unit tests
│       └── build-and-publish.yml   # Documentation fetch, pre-indexing & GHCR push
├── documentation/                  # Cloned during build / local dev
├── src/
│   └── obm_rag/
│       ├── __init__.py
│       ├── config.py               # Pydantic settings & paths
│       ├── ingestion/              # Ingestion, parsing, and chunking
│       │   ├── __init__.py
│       │   ├── models.py           # DocChunk dataclass
│       │   ├── rst_parser.py       # Sphinx RST & Markdown parser
│       │   └── indexer.py          # Vector embedding & ChromaDB persistence
│       ├── rag/                    # Retriever logic
│       │   ├── __init__.py
│       │   └── retriever.py        # Semantic search against ChromaDB
│       └── mcp/                    # MCP server
│           ├── __init__.py
│           ├── server.py           # Server instantiation & CLI transport
│           └── tools.py            # Tool implementations
├── scripts/
│   ├── build_index.py              # CLI index builder
│   └── test_query.py               # Interactive CLI test tool
├── data/
│   └── vector_store/               # ChromaDB storage (local / pre-baked)
├── tests/
│   ├── test_parser.py
│   ├── test_retriever.py
│   └── test_mcp_server.py
├── .dockerignore
├── .gitignore
├── Dockerfile                      # Multi-stage build with baked-in index
├── docker-compose.yml              # Server runtime configuration
├── pyproject.toml                  # Project definition & dependencies
└── uv.lock                         # Deterministic lockfile
```

---

## 4. Implementation Roadmap

### Phase 1: Ingestion & Parser
- [x] Configure `pyproject.toml` and lock dependencies via `uv`.
- [x] Implement `rst_parser.py` supporting Sphinx roles and Markdown hierarchy.
- [x] Build `build_index.py` and `indexer.py` with FastEmbed and ChromaDB.

### Phase 2: Retrieval & MCP Server
- [x] Implement `retriever.py` with cosine distance to relevance score mapping.
- [x] Implement `test_query.py` CLI testing utility.
- [x] Implement standard MCP server (`server.py`, `tools.py`) supporting STDIO, SSE, and Streamable HTTP.

### Phase 3: Packaging & CI/CD
- [x] Create multi-stage `Dockerfile` baking in pre-indexed documentation.
- [x] Create `docker-compose.yml` for zero-source server operation.
- [x] Implement GitHub Actions workflows (`ci.yml`, `build-and-publish.yml`).
- [x] Configure webhook trigger (`repository_dispatch`) for docs synchronization.
