# Subagent Orchestration Plan

**Use this plan when the parent Agent must run all subagents in tandem to build or refresh the app.**

---

## Ambitious Goal

**One-command production pipeline:** Ingest document(s) → extract covenants → run recovery waterfall → validate against market → stress-test → compare (prior/peers) → emit a single, auditable analyst report. Every step is versioned and reproducible.

---

## Current Implementation (as of last refresh)

The pipeline is **implemented in code**. One command runs all subagents in order; no separate AI invocations per subagent.

| How to run | Command |
| ---------- | ------- |
| **Single file** | `py -m signal_triage.cli <file> --pipeline` |
| **Batch folder** | `py -m signal_triage.cli --pipeline --batch <FOLDER>` (optional: `--recursive`) |
| **Skip Auditor gate** | Add `--no-audit-gate` to allow report when Critical Variance is unresolved |

**Output:** Single JSON auditable report (per doc or batch with `results`, `portfolio`, `comparator`). Exit code 1 when report is not published (Auditor gate failed).

**Code:** `signal_triage/pipeline.py` (`run_pipeline`, `run_pipeline_batch`); CLI in `signal_triage/cli.py` (`--pipeline`).

**When iterating:** Update `docs/ROADMAP.md` (phase status, todo) and this file (implementation status) so plans stay aligned with code.

---

## How to Run Subagents in Tandem

1. **Delegate by objective.** For each objective below, invoke the **named subagent** (e.g. "Using the **Author** subagent, …") so that agent runs with its own context and mandate. *In code:* the parent Agent implements or refines the logic for each objective; the pipeline runs them in sequence.
2. **Respect handoffs.** Each subagent consumes output from prior steps (see Handoffs below). Pass the relevant context when launching the next subagent.
3. **Run in order.** Execute objectives 1 → 7 so dependencies (e.g. Librarian → Quant → Auditor) are satisfied before downstream agents run.

---

## Objectives (Assign One per Subagent)

| # | Subagent | Objective |
|---|----------|-----------|
| 1 | **Author** | Implement or refine a single CLI entry point and versioned configs so the full pipeline can be run with one command. Ensure DocumentChunk ingestion has provenance for PDF/txt; web/URL and SEC EDGAR ingestion implemented in `ingest/web.py` (Phase 5). |
| 2 | **Librarian** | Wire covenant/basket extraction to the CLI and recovery path. Emit LME/collateral leakage flags for the Quant. Ensure JSON output includes section/page citation. |
| 3 | **Quant** | Maintain waterfall + fulcrum + EV sensitivity + tornado drivers (EV, collateral); apply LME-adjusted collateral when Librarian flags leakage. Use Decimal only for recovery math; optional tier/priority for Pari Passu pro-rata. Produce Situational Summary and tornado-ready output for the Reporter. |
| 4 | **Benchmarker** | Provide market multiples and precedent recovery rates with source citation. Flag Critical Variance when the Quant’s model diverges from market precedents. |
| 5 | **Auditor** | Stress-test the waterfall (scenarios, APR, Decimal precision). Reconcile Critical Variances; maintain audit trail (config version, document sources, market data dates). Act as gate for final report when required. |
| 6 | **Comparator** | Wire prior-vs-current (and, when data exists, vs peers) into the batch/CLI. Produce score/tier deltas and material-change narrative for the Reporter. |
| 7 | **Reporter** | Define and implement the formal "report per document" schema and portfolio summary format. Aggregate outputs from Librarian, Quant, Benchmarker, Comparator. Do not publish final report if Auditor has flagged (e.g. unresolved Critical Variance) when the process requires sign-off. |

---

## Handoffs (What Each Subagent Receives / Produces)

- **Author** → Librarian: Ingested chunks (and future web-sourced text) with provenance.
- **Librarian** → Quant: Baskets, covenant limits, LME/collateral leakage flags; JSON with section/page.
- **Quant** → Auditor: Recovery model, fulcrum, situational summary.
- **Benchmarker** → Quant: Market multiple (EV driver). Benchmarker → Auditor: Precedent recovery rates, Critical Variance flags.
- **Auditor** → Reporter: Pass/fail, audit trail; blocks publish when required.
- **Comparator** → Reporter: Prior/peer deltas, material-change narrative.
- **Reporter** → Analyst: Single report per document and portfolio summary; all content traceable to source.

---

## Source of Truth

The canonical roadmap and phase status live in **`docs/ROADMAP.md`**. When refreshing the roadmap or updating phase status, the parent Agent should:

1. Update **`docs/ROADMAP.md`**: phase status, High-Level Todo (strike done items, add next), Done section.
2. Update **this file (ORCHESTRATION.md)**: "Current Implementation" table (commands, code paths) so it matches the codebase.
3. Optionally update **`.cursor/agents/README.md`** if the agent list or flow changes.
