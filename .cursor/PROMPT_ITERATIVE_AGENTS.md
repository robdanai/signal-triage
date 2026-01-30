# Prompt: Iterative, multi-agent improvement of Signal Triage

**Use this prompt in Cursor to have the AI work iteratively, proactively, and as multiple agents writing code at length.** Paste the block below into a new chat, or say: "Follow @.cursor/PROMPT_ITERATIVE_AGENTS.md and run the full improvement cycle."

---

## The prompt (copy everything below this line)

You are improving the Signal Triage project iteratively and proactively. Work as if **multiple agents are writing code at the same time**: in one response, complete work for **at least two different agent roles** (e.g. Author + Librarian, or Quant + Auditor + Reporter). Do not stop after one file or one role. Produce **substantial, multi-file changes** each time.

**Rules:**
1. **Iterative:** Each response must make concrete progress (new or edited code, tests, or docs), then suggest or start the next logical step. Do not just plan—implement.
2. **Proactive:** Add tests for new or touched code, type hints and docstrings where missing, and update `docs/ROADMAP.md` or `.cursor/agents/ORCHESTRATION.md` when you change the pipeline or agent behavior. If you see dead code, unclear names, or missing error handling, fix them without being asked.
3. **Multi-agent at length:** In a single response, do work for **at least two** of the seven agents below. For each agent, edit or add **at least one file** (code or test or doc). Prefer three agents when feasible. Reference `.cursor/agents/<name>.md` for each agent’s mandate.

**The seven agents (roles and where they write):**
- **Author** – `signal_triage/ingest/` (reader, web stub), `signal_triage/cli.py`, pipeline config/versioning. Ensures one-command pipeline and provenance.
- **Librarian** – `signal_triage/document_intel/` (extractor, schema, patterns), `signal_triage/lme_parser.py`, `signal_triage/signals_io.py`. Covenant/basket extraction, section/page, collateral leakage flags.
- **Quant** – `signal_triage/recovery_engine.py`, Decimal-only recovery math, LME-adjusted EV, situational summary.
- **Benchmarker** – `signal_triage/agents/benchmarker.py`. Market multiples, precedents, Critical Variance flags, source citation.
- **Auditor** – `signal_triage/agents/auditor.py`. Stress-test, Critical Variance reconciliation, audit trail, gate for Reporter.
- **Comparator** – `signal_triage/agents/comparator.py`. Prior vs current (and peers when data exists), score/tier deltas, material-change narrative.
- **Reporter** – `signal_triage/reports/document_report.py`, `signal_triage/agents/batch_portfolio.py`, `signal_triage/agents/summary_narrative.py`. Auditable report schema, portfolio summary, Auditor gate.

**Concrete cycle for this session:**
1. Pick **two or three** agents that have clear next steps (from `docs/ROADMAP.md` “Next” items or obvious gaps: tests, types, docs, or ROADMAP todo).
2. For each chosen agent, implement or refine code in their owned paths, add or update at least one test in `tests/`, and update docs if needed.
3. Run the pipeline once to confirm no regression: `py -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline` (or `--pipeline --batch tests/fixtures/benchmark_corpus`).
4. At the end of your response, list **next suggested improvements** (by agent) so the next turn can continue iteratively.

**Start now:** Read `docs/ROADMAP.md` and `.cursor/agents/ORCHESTRATION.md`, then execute one full cycle (at least two agents, multi-file, with tests and a pipeline run). Do not summarize without coding—produce diffs and new files.

---

*End of prompt*
