# Distressed Subagent Team

Seven specialized agents for Signal Triage / distressed debt analysis. Run in tandem using the objectives and order in **ORCHESTRATION.md** and **docs/ROADMAP.md**.

---

## Step-by-step: What you do to make all agents work and hit the goals

**Goal:** One-command pipeline that ingests document(s) → extracts covenants → runs recovery waterfall → validates vs market → stress-tests → compares (prior/peers when available) → emits a single, auditable analyst report.

### 1. Run the full pipeline (all agents in order)

From the project root:

| What you want | What you run |
|---------------|--------------|
| **One document** (e.g. a Credit Agreement PDF or .txt) | `py -m signal_triage.cli path/to/file.pdf --pipeline` |
| **A folder of documents** (batch; Comparator runs when 2+ files) | `py -m signal_triage.cli --pipeline --batch path/to/folder` |
| **Batch including subfolders** | `py -m signal_triage.cli --pipeline --batch path/to/folder --recursive` |

That single command runs, in order: **Author** (ingest) → **Librarian** (covenants, leakage flags) → **Quant** (waterfall, situational summary) → **Benchmarker** (market/precedent, Critical Variance) → **Auditor** (stress-test, audit trail, gate) → **Comparator** (only in batch with 2+ docs) → **Reporter** (single auditable report). You get one JSON report to stdout.

### 2. Interpret the result

- **Exit code 0:** Report was **published** (Auditor passed or gate not required).
- **Exit code 1:** Report was **not published** because the Auditor gate failed (e.g. unresolved Critical Variance). The JSON still contains the full report; use `auditor_summary.passed` and `published` to see why.
- **To allow “publish” even when Critical Variance is unresolved** (e.g. for drafts): add `--no-audit-gate` to the command.

### 3. Optional: filter by industry/geography

For Benchmarker (market multiples, precedents):

- `py -m signal_triage.cli path/to/file.pdf --pipeline --industry Retail --geography US`

### 4. When you change code or the pipeline

Keep the plans aligned with reality:

1. Update **`docs/ROADMAP.md`**: phase status, High-Level Todo (strike done, add next), Done section.
2. Update **`.cursor/agents/ORCHESTRATION.md`**: “Current Implementation” table (commands, code paths).
3. Optionally update this **README** if the agent list or flow changes.

---

## Agent roles and flow

| Agent | Role |
|-------|------|
| **author** | Ingestion, APIs & tooling; document pipeline; EDGAR/data providers; versioned configs; single CLI entry point. |
| **librarian** | Document intelligence; covenant & basket extraction; "trap doors" and collateral leakage. |
| **quant** | Waterfall & sensitivity; recovery engine, fulcrum, EV scenarios; Decimal math; Situational Summary. |
| **benchmarker** | Market context & precedents; recovery benchmarking; yield spreads, ratings, multiples; Critical Variance flags. |
| **auditor** | Stress-testing & validation; variance checks; reproducibility & audit trail; gate for final report. |
| **comparator** | Prior vs current, vs peers; score/tier deltas; new/removed signals; material-change narrative. |
| **reporter** | Per-doc report, portfolio summary; analyst-facing output; narrative consistency; aggregates all agents. |

**Flow (run order):** Author → Librarian → Quant ← Benchmarker → Auditor; Comparator feeds Reporter; Reporter assembles final output. See **ORCHESTRATION.md** for objectives per agent and handoffs.
