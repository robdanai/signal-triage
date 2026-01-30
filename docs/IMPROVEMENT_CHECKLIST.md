# Improvement checklist

Use this when touching code so the project stays consistent and auditable. Cursor (or a human) can apply it after changes.

---

## When adding or changing code

- [ ] **Tests:** New or touched logic has a test in `tests/` (e.g. `test_<module>.py`). Run: `py -m pytest tests/ -v` (or `python -m unittest discover -s tests`).
- [ ] **Types:** New or modified function signatures have type hints (args and return).
- [ ] **Docstrings:** Public functions and classes have a one-line docstring (and optional Args/Returns for non-trivial functions).
- [ ] **Pipeline:** After pipeline/CLI changes, run once: `py -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline` or `--pipeline --batch tests/fixtures/benchmark_corpus`.
- [ ] **Docs:** If pipeline or agent behavior changed, update `docs/ROADMAP.md` (phase status, todo) and `.cursor/agents/ORCHESTRATION.md` (Current Implementation) so plans match code.

---

## Agent-owned areas (do not break handoffs)

- **Author:** Ingestion has provenance; config versions still captured in audit trail; `--pipeline` still runs full chain.
- **Librarian:** Extraction still emits section/page and `collateral_leakage_flags` in JSON/signals.
- **Quant:** Recovery math still uses `Decimal`; waterfall result still has `situational_summary` when from signals.
- **Auditor:** Stress test and audit trail still run; Reporter still respects gate when `require_audit_gate` is True.
- **Reporter:** Auditable report still has `document`, `audit_trail`, `published`, and agent summaries when provided.

---

## Quick commands

| Action              | Command |
|---------------------|--------|
| Run pipeline (one file) | `py -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline` |
| Run pipeline (batch)   | `py -m signal_triage.cli --pipeline --batch tests/fixtures/benchmark_corpus` |
| Run tests              | `py -m pytest tests/ -v` or `py -m unittest discover -s tests -v` |
