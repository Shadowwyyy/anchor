# Anchor

**Clear, cited answers about U.S. immigration status for international students and non-citizens.**

Anchor is a retrieval-augmented (RAG) assistant that answers questions about F-1 rules, work authorization, travel, and related topics — grounded strictly in official source documents, with citations and a *refuse-to-guess* safety gate that declines rather than answer from weak evidence.

> **Informational only — not legal advice.** Immigration rules change frequently and are highly case-specific. Anchor surfaces official guidance with citations; it does not replace an immigration attorney or a school's DSO.

---

## Why this project

Immigration guidance is scattered, dense, and changes often. Anchor consolidates official documents and answers plain-language questions **with citations back to the source**, refusing to answer when it isn't confident — because on questions that affect someone's legal status, a confident wrong answer is worse than an honest "I'm not sure."

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
 (Chroma)       (refuse-to-guess)       + model-refusal check   or refusal
```

- **Embeddings run locally** via [Ollama](https://ollama.com) (`nomic-embed-text`) — no embedding API, no per-token cost, fully offline.
- **Generation** uses Claude Haiku via the Anthropic API — cost-efficient and well-suited to extracting facts from provided context.
- **Vector store** is Chroma (persistent, cosine distance).
- **Two-layer refusal:** a cheap distance pre-filter declines clearly-unrelated questions before any API call; the model's own grounded refusal ("the provided context does not cover…") catches questions that are semantically close but not actually covered.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Embeddings | Ollama (`nomic-embed-text`), local |
| Vector store | Chroma (persistent, cosine) |
| Generation | Claude Haiku (Anthropic API) |
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
│   ├── confidence.py       # distance-based refuse-to-guess gate
│   ├── generate.py         # grounded prompt, Claude call, model-refusal check
│   ├── service.py          # orchestrates the ask flow
│   ├── app.py              # FastAPI service (/health, /ask)
│   ├── main.py             # ingest entry point
│   └── test_*.py           # unit tests for every component
├── eval/                   # evaluation harness
│   ├── questions.jsonl     # labeled question set
│   └── run_eval.py         # runs questions through the live API and scores
├── frontend/               # Next.js app (chat UI)
│   └── src/app/
├── data/                   # source documents, manifest, persisted store
│   └── sources.json        # provenance: URL + fetch date per document
├── pyproject.toml
└── requirements.txt
```

---

## Design notes

**Dependency injection throughout.** Every component that touches the network or disk — the tokenizer, PDF reader, embedder, Chroma collection, Claude client — is injected rather than imported directly. This keeps the entire test suite fast and offline: fakes stand in for real services, and the real adapters are thin.

**The confidence gate is separated on purpose.** Refuse-to-guess is the safety-critical piece, reused across every answer path, so it lives in its own tested module (`confidence.py`) rather than being buried inside generation.

**Two-layer refusal.** Distance alone can't separate on-topic from off-topic questions, because a question like "Can I rent a car on an F-1 visa?" embeds close to the F-1 documents even though the answer isn't in them. Anchor combines a distance pre-filter (cheap, catches clearly-unrelated questions before an API call) with detection of the model's own grounded refusal.

**Cosine distance, calibrated.** Chroma defaults to squared-L2, which is wrong for `nomic-embed-text` (meant for cosine) — the collection is explicitly created with cosine distance. Strong topical matches score ~0.2; the refusal threshold sits at 0.5.

**PDF cleaning.** Print-to-PDF injects headers (timestamps, page numbers) into extracted text; the loader strips these so they don't crowd out real content and degrade retrieval.

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

Every pipeline component is unit-tested with faked dependencies — no network, no live Ollama or Claude required. Coverage includes chunking edge cases (overlap, boundaries, empty input), document cleaning, the confidence threshold boundaries, model-refusal detection, and the refuse-to-guess paths (verifying Claude is never called on a low-confidence refusal).

---

## Evaluation

Anchor is evaluated against a labeled question set that runs through the live API and scores three things independently: whether the system correctly answered vs. refused, whether it cited the right source document, and whether the answer contained the expected fact.

The set has 22 questions across three buckets:
- **Answerable** — questions whose answer is in the corpus (e.g. "How long is the STEM OPT extension?")
- **Refusal** — questions genuinely outside the corpus that should be declined (e.g. "What's the weather today?")
- **Edge** — boundary cases that stress retrieval and the confidence gate

### Results

| Metric | Score |
|--------|-------|
| Content accuracy (expected fact present) | 100% |
| Source accuracy (correct document cited) | 95% |
| Refusal accuracy (answered vs. refused correctly) | 91% |
| **Fully correct (all three)** | **91%** |

Run it with the API up:

```bash
python -m eval.run_eval
```

### What the eval caught

The eval surfaced real weaknesses that were then fixed:

- **The confidence gate was too permissive.** Off-topic-but-similar questions ("Can I rent a car on an F-1 visa?") scored low embedding distances because they mention F-1 visas, so a distance threshold alone let them through. The fix was the two-layer refusal described above.
- **PDF extraction was polluting chunks.** "Save as PDF" injected print-dialog headers into the text, crowding out real content and degrading retrieval. The loader now strips these artifacts.
- **A coverage gap.** The on-campus 20-hour work rule wasn't answerable because the source page's content was hidden behind collapsible sections that didn't render on print. Caught by the eval, fixed by adding the missing source.

### Known limitations

The remaining failures are near-threshold retrieval variance: questions right at the edge of the corpus behave non-deterministically because embedding distance is a fuzzy signal. A question whose relevant chunk ranks just inside or just outside the top-k can flip between answering and refusing across runs. This is an inherent property of distance-based RAG confidence rather than a discrete bug, and it's the natural next target for improvement (e.g. a reranking step or a learned confidence signal).

---

## Roadmap

- A reranking step to reduce near-threshold retrieval variance.
- Additional modes on the same backbone: document checklist, status-pathway explainer, and an eligibility/timeline assistant with deterministic date logic.
- Per-IP and global rate limiting ahead of a public deployment.
- Conversational follow-ups (context-aware multi-turn questions).

---

## Disclaimer

Anchor is for **informational and educational purposes only** and does **not** constitute legal advice. Immigration law and policy change frequently and depend on individual circumstances. Always verify against the official government source and consult a licensed immigration attorney and your school's Designated School Official (DSO).
