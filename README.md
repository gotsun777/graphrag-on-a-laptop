# GraphRAG on a Laptop

**Companion code for the book *GraphRAG on a Laptop: Build, Break, and Honestly Measure an Ontology-Driven Question-Answering System with Neo4j and Ollama.***

No GPU. No cloud. No hand-waving. Every script in this repository is the exact version that produced the book's lab record — including the round the graph lost.

![Python](https://img.shields.io/badge/python-3.13-blue) ![neo4j--graphrag](https://img.shields.io/badge/neo4j--graphrag-1.19.0-018bff) ![GPU](https://img.shields.io/badge/GPU-not%20required-2ea043)

---

## The experiment in one table

Ten fixed questions were put to the same corpus three times, on a four-core laptop (i5-10210U, 16 GB RAM, no GPU):

| Round | Retrieval | Graph state | Result |
|---|---|---|---|
| **R1** | Vector only | rough (47% chunks entity-less, 36 duplicate-ridden Regulation nodes) | 6 correct / 3 partial / 1 near-wrong — one **spliced fact** (two true numbers welded into a false one) |
| **R2** | Vector + graph, unbounded query | rough (same) | **Loses to its own baseline** — surrenders on a question the corpus answers, and cites statutes that don't exist |
| **R3** | Vector + graph, capped & typed query | clean (text eye-reviewed, rebuilt 17.6 h, entities merged in ~1 s) | **8 correct / 2 partial / 0 failures** — the only clean scorecard, at +15% answer time |

The finding, earned rather than assumed:

> **Graph retrieval is not an upgrade you install. It is a quality you maintain.**

## What's in this repository

```
graphrag-on-a-laptop/
├── ontology.py            # Schema v0.2 — 8 node types, 10 relationships, frozen
├── common.py              # .env loading, fail-fast driver, append-only logger
├── queries.py             # The 10 evaluation questions + retrieval query v2
├── check_connection.py    # Verify the triangle: Neo4j / embeddings / LLM
├── probe_nothink.py       # Verify /no_think yields parseable JSON
├── clean_extract.py       # PDF → cleaned per-chapter texts (+ eye-review checklist)
├── create_index.py        # Vector index (run once; survives data wipes)
├── rebuild_kg.py          # Canonical builder: snapshot → wipe → build, one event loop
├── merge_entities.py      # Entity resolution by curation (the one-second fix)
├── eval_round3.py         # Two-arm evaluation harness (vector, then graph v2)
├── ask.py                 # Single-question CLI:  python ask.py "..." [--graph]
├── cypher/
│   └── workbench.md       # Appendix B: health check · contents · visualization · ontology audit
├── transcripts/
│   ├── eval_results.md    # All 40 answers across three rounds, verbatim, with timings
│   └── build_log.txt      # Every extraction run, timestamped, failures included
├── .env.example           # Copy to .env and fill in — never commit .env
└── README.md
```

## Requirements

| Component | Version used in the book | Notes |
|---|---|---|
| Python | 3.13 | 3.10+ should work |
| [Neo4j Desktop](https://neo4j.com/download/) | DB 2026.08.1, **APOC installed** | APOC is required by `merge_entities.py` |
| [Ollama](https://ollama.com/) | with `qwen3:8b` and `bge-m3` | `ollama pull qwen3:8b && ollama pull bge-m3` |
| `neo4j-graphrag` | **1.19.0** | Pinned deliberately — Chapter 4 documents a version-specific behavior |

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install neo4j-graphrag==1.19.0 pymupdf python-dotenv
cp .env.example .env                # then edit .env
```

**Hardware honesty:** every timing below was measured on a four-core laptop CPU. A GPU changes the speed (dramatically), not the method — the ontology, the cleaning pass, the entity merge, the query discipline, and the two-arm evaluation are identical either way.

## Reproduction order

The order is the finding — curation sits *between* the two evaluation runs on purpose:

```bash
python check_connection.py    # Step 1 — three green checks
python probe_nothink.py       # Step 1 — /no_think verified before trusting a night to it
#                               Step 2 — edit ontology.py for YOUR domain, then freeze it
python clean_extract.py       # Step 3 — then EYE-REVIEW the clean_*.txt files (30 min, not optional)
python create_index.py        # once per database
python rebuild_kg.py          # Steps 4–6 — overnight; read build_log.txt in the morning
python eval_round3.py         # Step 7 — baseline first (the vector arm runs first)
#                               Step 8 — print entity names (cypher/workbench.md, B2-1), edit merge groups
python merge_entities.py
python eval_round3.py         # Steps 9–10 — both arms again, on the merged graph
```

## What it costs (measured, not estimated)

| Step | Cost on the reference machine |
|---|---|
| Extraction | 25–50 min **per chunk** → a 5-chapter, ~55k-char corpus ≈ 2–3 overnights per full build |
| Extraction failure rate | 45–55% of chunks, in every configuration — an 8B-model JSON ceiling, not a text problem |
| Entity merge | ~1 second |
| Retrieval-query rewrite | ~10 minutes |
| Evaluation | 8–15 min per question per arm → one 10-question two-arm round ≈ 4 hours |
| Graph context premium at answer time | ~+15% over plain vectors, with a capped, typed query |

The expensive step is the one everyone plans for. The outcome was decided by the cheap ones.

## Adapting this to your own corpus

1. **Pick a corpus you can grade.** The book's entire evaluation method rests on the grader knowing the corpus cold — the author used his own previous book. A corpus you can't fact-check gives you a demo, not an experiment.
2. `clean_extract.py` — replace `PDF_PATH` and the page ranges; your running-head regex will differ.
3. `ontology.py` — rewrite the node/relationship types for your domain (design for your *questions*, not your documents), then freeze it.
4. `queries.py` — write your own 10 questions in three tiers: single-fact, relational, multi-hop synthesis. Include at least one trap.
5. `merge_entities.py` — your merge groups will differ; the method transfers: print the names, read the list, write the groups. Match strings byte-for-byte (em dashes and curly apostrophes included).

## Known limits (printed, not hidden)

- **Graph expansion inherits the biases of its vector entry.** One question (T3-8) failed in every configuration because its key term never survives the embedding-similarity entry stage. A cleaner graph cannot fix an entry that never reaches the right chunks.
- **An index rebuild is a breaking change.** Chunk boundaries are retrieval-relevant state; one question (T3-9) regressed in *both* arms after the rebuild. Re-run the full two-arm evaluation after every rebuild.
- **The 8B JSON ceiling.** ~45% of chunks fail structured extraction regardless of text cleaning. Failed chunks keep their text and embeddings, so vector retrieval survives; the graph is thinner than the corpus, and — as Round 3 shows — a thin clean graph beats a thick dirty one.

## The book

This repository accompanies **_GraphRAG on a Laptop_** (First Edition, 2026) by **Dr. Woongsik Su, MBA**, which tells the whole story: the stack and its traps, the ontology design, the batch nights, the quality loop, all three evaluation rounds graded answer by answer, the recipe, and the limits. The corpus indexed throughout is the author's previous book, *The Executive's Guide to Global AI Governance* — chosen because an evaluation is only as honest as its grader.

<!-- TODO: add purchase/landing link when available -->

## Citation

```bibtex
@book{su2026graphrag,
  author    = {Su, Woongsik},
  title     = {GraphRAG on a Laptop: Build, Break, and Honestly Measure an
               Ontology-Driven Question-Answering System with Neo4j and Ollama},
  year      = {2026},
  edition   = {First},
  note      = {Companion code: https://github.com/OWNER/graphrag-on-a-laptop}
}
```

## License

- **Code** (`*.py`, `cypher/`): MIT License — see [`LICENSE`](LICENSE).
- **Transcripts and logs** (`transcripts/`): © 2026 Woongsik Su. Provided for verification and study alongside the book; all rights reserved.

Quoted system outputs in the transcripts include answers that are factually wrong — fabricated statute names, spliced fine amounts. They are preserved *because* they are wrong; that is the subject of the book. Nothing in them should be relied on as information about AI regulation.
