# Anchor

**Clear, cited answers about U.S. immigration status for international students and non-citizens.**

Anchor is a retrieval-augmented (RAG) assistant that answers questions about F-1 rules, work authorization, travel, and related topics — grounded strictly in official source documents, with citations and a *refuse-to-guess* safety gate that declines rather than answer from weak evidence.

> **Informational only — not legal advice.** Immigration rules change frequently and are highly case-specific. Anchor surfaces official guidance with citations; it does not replace an immigration attorney or a school's DSO.

---

## Why this project

Immigration guidance is scattered, dense, and changes often. Anchor consolidates official documents and answers plain-language questions **with citations back to the source**, refusing to answer when its retrieval confidence is low — because on questions that affect someone's legal status, a confident wrong answer is worse than an honest "I'm not sure."

The refuse-to-guess behavior is a first-class, visible feature: a grounded answer and a refusal render as visibly different states in the UI.

---

## Architecture

Anchor separates a local ingestion/retrieval pipeline from generation, so embeddings run fully offline and only the final answer step calls a hosted model.

```
Documents (.pdf/.txt/.md)
        |
        v
   loader  -->  chunker  -->  embedder        -->  Chroma
   (clean)      (tokens)      (Ollama, local)      (store)

Question
    |
    v
 retrieve  -->  assess_confidence  -->  generate (Claude)  -->  cited answer
 (Chroma)       (refuse-to-guess)                                or refusal
```

- **Embeddings run locally** via [Ollama](https://ollama.com) (`nomic-embed-text`) — no embedding API, no per-token cost, fully offline.
- **Generation** uses Claude via the Anthropic API, with a grounded prompt that answers only from retrieved context.
- **Vector store** is Chroma (persistent, cosine distance).
- **The confidence gate** is a separate, independently tested component: if the nearest chunk's distance exceeds a threshold, Anchor declines instead of generating.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Embeddings | Ollama (`nomic-embed-text`), local |
| Vector store | Chroma (persistent, cosine) |
| Generation | Claude (Anthropic API) |
| API | FastAPI |
| Frontend | Next.js (App Router, TypeScript) |
| Tests | pytest |

---

## Project layout

```
anchor/
├── ingest/                 # Python package: the full RAG pipeline
│   ├── loader.py           # read + clean pdf/txt/md
│   ├── chunker.py          # token-based chunking with overlap
│   ├── embedder.py         # local Ollama embeddings
│   ├── store.py            # write chunks + metadata to Chroma
│   ├── retriever.py        # embed query, return top-k with sources
│   ├── confidence.py       # refuse-to-guess gate
│   ├── generate.py         # grounded prompt + Claude call, or refusal
│   ├── service.py          # orchestrates the ask flow
│   ├── app.py              # FastAPI service (/health, /ask)
│   ├── main.py             # ingest entry point
│   └── test_*.py           # unit tests for every component
├── frontend/               # Next.js app (chat UI)
│   └── src/app/
├── data/                   # source documents + persisted Chroma store
├── pyproject.toml
└── requirements.txt
```

---

## Design notes

**Dependency injection throughout.** Every component that touches the network or disk — the tokenizer, PDF reader, embedder, Chroma collection, Claude client — is injected rather than imported directly. This keeps the entire test suite fast and offline: fakes stand in for real services, and the real adapters are thin.

**The confidence gate is separated on purpose.** Refuse-to-guess is the safety-critical piece, reused across every answer path, so it lives in its own tested module (`confidence.py`) rather than being buried inside generation.

**Cosine distance, calibrated.** Chroma defaults to squared-L2, which is wrong for `nomic-embed-text` (meant for cosine) — the collection is explicitly created with cosine distance. Strong topical matches score ~0.2; the refusal threshold sits at 0.6, leaving room for looser-but-valid phrasings while rejecting off-topic questions.

---

## Running locally

**Prerequisites:** Python 3.12+, Node 18+, [Ollama](https://ollama.com) running locally, and an Anthropic API key.

**1. Backend setup**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
ollama pull nomic-embed-text
```

Create a `.env` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

**2. Ingest documents**

Drop `.pdf`, `.txt`, or `.md` files into `data/`, then:

```bash
python -m ingest.main
```

**3. Run the API**

```bash
uvicorn ingest.app:app --reload --port 8000
```

Interactive docs at `http://localhost:8000/docs`.

**4. Run the frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Tests

```bash
python -m pytest -v
```

Every pipeline component is unit-tested with faked dependencies — no network, no live Ollama or Claude required. Coverage includes chunking edge cases (overlap, boundaries, empty input), document cleaning, the confidence threshold boundaries, and the refuse-to-guess paths (verifying Claude is never called on a refusal).

---

## Roadmap

- Ingest the full set of official USCIS / SEVP / Study in the States sources with a dated manifest for freshness tracking.
- Additional modes on the same backbone: document checklist, status-pathway explainer, and an eligibility/timeline assistant with deterministic date logic.
- An evaluation set of real questions to calibrate the confidence threshold and measure retrieval accuracy + correct-refusal rate.
- Markdown rendering and response-length tuning in the UI.

---

## Disclaimer

Anchor is for **informational and educational purposes only** and does **not** constitute legal advice. Immigration law and policy change frequently and depend on individual circumstances. Always verify against the official government source and consult a licensed immigration attorney and your school's Designated School Official (DSO).
