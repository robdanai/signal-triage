# Config Versioning

Model and scoring behavior are driven by `signals_config.json` and `settings.json`. Both configs support a **version** field for reproducibility and auditability.

## Version field

- **signals_config.json**: optional top-level key `"version"` (e.g. `"1.0"`). Exposed via `signal_triage.signals_loader.get_signals_config_version()`.
- **settings.json**: optional top-level key `"version"` (e.g. `"1.0"`). Included in the dict returned by `load_settings()` under the key `"version"`.

## Semantics

- **Reproducibility**: When reporting scores or running benchmarks, record the config version(s) so the same results can be reproduced later.
- **Auditability**: Versioned configs allow audits to identify which rule set and tier thresholds were used for a given run.
- **Naming**: Use semantic-style versions (e.g. `1.0`, `1.1`). Bump the version when you change signal rules, weights, or tier boundaries in a way that affects scoring.

## Benchmark corpus

The benchmark corpus under `tests/fixtures/benchmark_corpus/` includes a `manifest.json` with its own `version`. Use it to validate that scoring behavior stays within expected ranges when configs or code change.
