"""
Command-line interface for Signal Triage.
Handles user input and output.
"""

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from signal_triage.analyzer import analyze_text
from signal_triage.recovery_engine import run_waterfall, run_waterfall_from_signals, ev_sensitivity, tornado_drivers
from signal_triage.document_intel.extractor import extract_baskets_and_covenants
from signal_triage.signals_io import scan_document_and_write_signals
from signal_triage.agents.benchmarker import run_benchmarker
from signal_triage.ingest.reader import read_document, full_text
from signal_triage.reports.document_report import build_document_report, build_error_report
from signal_triage.agents.batch_portfolio import run_batch_portfolio
from signal_triage.pipeline import run_pipeline, run_pipeline_batch, write_run_manifest, _is_url, _is_edgar_accession
from signal_triage.adversarial_forensics import perform_adversarial_forensics
from signal_triage.stress_test import run_priming_stress_test
from signal_triage.agents.evidence_verifier import run_evidence_verifier

BATCH_SUFFIXES = (".txt", ".pdf")


def _json_default(obj):
    """JSON encoder default: Decimal -> float so recovery_engine output is serializable."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _parse_tranches(s: str) -> list[dict]:
    """Parse 'Name:Claim,Name:Claim' into list of {name, claim}."""
    out = []
    for part in s.split(","):
        part = part.strip()
        if ":" in part:
            name, claim_str = part.split(":", 1)
            try:
                claim = float(claim_str.strip())
            except ValueError:
                claim = 0.0
            out.append({"name": name.strip(), "claim": claim})
    return out


def _discover_batch_files(folder: Path, recursive: bool) -> list[Path]:
    """Return sorted list of .txt and .pdf paths in folder (optionally recursive)."""
    paths = []
    if recursive:
        for ext in BATCH_SUFFIXES:
            paths.extend(folder.rglob(f"*{ext}"))
    else:
        for p in folder.iterdir():
            if p.is_file() and (p.suffix or "").lower() in BATCH_SUFFIXES:
                paths.append(p)
    return sorted(paths, key=lambda p: (p.name.lower(), str(p)))


def _run_batch(
    folder_path: Path,
    recursive: bool,
    as_json: bool,
    verbose: bool,
    report_per_doc: bool = False,
) -> int:
    """Process all supported files in folder; print summary report. Returns exit code."""
    if not folder_path.is_dir():
        print(f"Error: Batch path is not a directory: {folder_path}", file=sys.stderr)
        return 1
    files = _discover_batch_files(folder_path, recursive)
    if not files:
        print(f"No .txt or .pdf files found in {folder_path}", file=sys.stderr)
        return 1
    results = []
    for fp in files:
        try:
            chunks = read_document(fp)
            text = full_text(chunks)
        except Exception as e:
            if verbose:
                print(f"Skip {fp}: {e}", file=sys.stderr)
            results.append({
                "file": str(fp),
                "error": str(e),
                "score": None,
                "tier": None,
                "tier_label": None,
                "text_length": 0,
                "top_signals": [],
                "evidence_snippets": [],
                "provenance": {"source_path": str(fp), "text_length": 0},
            })
            continue
        result = analyze_text(text)
        report = build_document_report(result, source_path=str(fp), text_length=len(text))
        results.append(report)
    # Sort by score descending (None/errors last)
    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    total = len(results)
    ok = [r for r in results if r["score"] is not None]
    n_ok = len(ok)
    avg_score = sum(r["score"] for r in ok) / n_ok if n_ok else 0.0
    min_score = min(r["score"] for r in ok) if n_ok else None
    max_score = max(r["score"] for r in ok) if n_ok else None
    summary = {
        "folder": str(folder_path),
        "total_files": total,
        "processed": n_ok,
        "errors": total - n_ok,
        "avg_score": round(avg_score, 2) if n_ok else None,
        "min_score": round(min_score, 2) if min_score is not None else None,
        "max_score": round(max_score, 2) if max_score is not None else None,
    }
    if as_json:
        # Emit formal report-per-document format; align portfolio summary with same shape.
        portfolio = run_batch_portfolio(results, id_key="file", score_key="score", top_n=10)
        out = {
            "report_format": "document_report",
            "summary": summary,
            "results": results,
            "portfolio": {
                "ranked": portfolio["ranked"],
                "top_risks": portfolio["top_risks"],
                "summary": portfolio["summary"],
            },
        }
        print(json.dumps(out, indent=2))
        return 0
    # Human-readable summary report
    print("Batch summary report")
    print(f"Folder: {folder_path}")
    print(f"Files processed: {n_ok}/{total}" + (f" ({total - n_ok} errors)" if total - n_ok else ""))
    if n_ok:
        print(f"Score range: {min_score:.2f} - {max_score:.2f}  (avg: {avg_score:.2f})")
    print()
    print(f"{'File':<50} {'Score':>8} {'Tier':<12}")
    print("-" * 72)
    for r in results:
        name = Path(r["file"]).name
        if len(name) > 48:
            name = "..." + name[-45:]
        if r["score"] is not None:
            tier = (r.get("tier_label") or r.get("tier") or "").strip() or "-"
            print(f"{name:<50} {r['score']:>8.2f} {tier:<12}")
        else:
            print(f"{name:<50} {'(error)':>8} {r.get('error', '')[:20]:<12}")
    # Report per document: score, tier, top signals, evidence snippets, provenance
    if report_per_doc and results:
        print()
        for r in results:
            p = r.get("provenance") or {}
            src = p.get("source_path") or r.get("file") or "—"
            print("---")
            print(f"Document: {src}")
            print(f"  Score: {r.get('score')}  Tier: {r.get('tier_label') or r.get('tier') or '—'}")
            print(f"  Provenance: {p.get('text_length', 0)} chars")
            for s in (r.get("top_signals") or [])[:5]:
                ev = (s.get("evidence") or "")[:80]
                print(f"  Signal: {s.get('type', '')} | {ev}{'...' if len(s.get('evidence') or '') > 80 else ''}")
            for i, snip in enumerate((r.get("evidence_snippets") or [])[:3], 1):
                out = snip[:100] + ("..." if len(snip) > 100 else "")
                print(f"  Evidence {i}: {out}")
            if r.get("score") is None and r.get("error"):
                print(f"  Error: {r['error']}")
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze a text file and calculate a distress score, or run a recovery waterfall."
    )
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        default=None,
        help="Path to the text or PDF file to analyze (omit for waterfall)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--checklist-only",
        action="store_true",
        help="Print only analyst to-do checklist (one item per line)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print Summary & Risk Narrative only (concise analyst-facing overview)",
    )
    parser.add_argument(
        "--waterfall",
        action="store_true",
        help="Run recovery waterfall instead of file analysis",
    )
    parser.add_argument(
        "--ev",
        type=float,
        default=None,
        help="Enterprise value (required for --waterfall)",
    )
    parser.add_argument(
        "--tranches",
        type=str,
        default=None,
        help="Tranches as Name:Claim,Name:Claim (e.g. Senior:300,Mezz:200,Unsecured:150)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON (for analyst/Quant Agent integration)",
    )
    parser.add_argument(
        "--librarian",
        action="store_true",
        help="Distressed Librarian: extract Negative Covenants and Baskets (JSON output with citations)",
    )
    parser.add_argument(
        "--benchmarker",
        action="store_true",
        help="Distressed Benchmarker: run market/precedent check (use with --waterfall to validate recoveries)",
    )
    parser.add_argument(
        "--industry",
        type=str,
        default=None,
        help="Industry filter for benchmarker (e.g. Retail)",
    )
    parser.add_argument(
        "--geography",
        type=str,
        default=None,
        help="Geography filter for benchmarker (e.g. US)",
    )
    parser.add_argument(
        "--from-signals",
        action="store_true",
        help="Use capital structure and default EV from signals.json (Librarian handoff)",
    )
    parser.add_argument(
        "--signals-path",
        type=str,
        default="signals.json",
        help="Path to signals.json (default: signals.json)",
    )
    parser.add_argument(
        "--sensitivity",
        action="store_true",
        help="Run EV sensitivity analysis around base EV (with --waterfall)",
    )
    parser.add_argument(
        "--tornado",
        action="store_true",
        help="Run tornado drivers (EV and optional collateral adjustment) for diagram (with --waterfall)",
    )
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        metavar="FOLDER",
        help="Process all .txt and .pdf files in FOLDER and print a summary report",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="With --batch: include files in subfolders (default: top-level only)",
    )
    parser.add_argument(
        "--report-per-doc",
        action="store_true",
        help="With --batch: print a report per document (score, tier, top signals, evidence, provenance)",
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run full production pipeline: ingest → librarian → quant → benchmarker → auditor → comparator → reporter; emit single auditable report (use with file or --batch)",
    )
    parser.add_argument(
        "--no-audit-gate",
        action="store_true",
        help="With --pipeline: do not block report when Auditor flags Critical Variance (default: block)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        metavar="REPORT.json",
        help="With --pipeline: write report to REPORT.json and run_manifest.json next to it for reproducibility",
    )
    parser.add_argument(
        "--url",
        action="store_true",
        help="With --pipeline: treat the positional argument as an http(s) URL to ingest (Phase 5)",
    )
    parser.add_argument(
        "--edgar",
        action="store_true",
        help="With --pipeline: treat the positional argument as an SEC EDGAR accession (e.g. 0001234567-21-000789)",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="With --pipeline and URL/EDGAR: directory to cache fetched content (default: no cache)",
    )
    
    # NEW: Forensic analysis options
    parser.add_argument(
        "--covenant-headroom",
        action="store_true",
        help="With --pipeline: calculate covenant headroom (requires --covenant-ebitda, --covenant-debt, --covenant-max-leverage)",
    )
    parser.add_argument(
        "--covenant-ebitda",
        type=float,
        default=None,
        help="Reported EBITDA for covenant headroom calculation",
    )
    parser.add_argument(
        "--covenant-debt",
        type=float,
        default=None,
        help="Total debt for covenant headroom calculation",
    )
    parser.add_argument(
        "--covenant-max-leverage",
        type=float,
        default=None,
        help="Maximum leverage covenant (e.g. 6.0 for 6.0x)",
    )
    parser.add_argument(
        "--covenant-addbacks",
        type=str,
        default=None,
        help="EBITDA add-backs as JSON string (e.g. '{\"run_rate_synergies\": 20, \"one_time_charges\": 5}')",
    )
    parser.add_argument(
        "--ch11-feasibility",
        action="store_true",
        help="With --pipeline: assess Ch. 11 reorganization feasibility (requires --ch11-gc-ev, --ch11-secured-debt, --ch11-total-debt)",
    )
    parser.add_argument(
        "--ch11-gc-ev",
        type=float,
        default=None,
        help="Going concern enterprise value for Ch. 11 feasibility",
    )
    parser.add_argument(
        "--ch11-secured-debt",
        type=float,
        default=None,
        help="Secured debt balance for Ch. 11 feasibility",
    )
    parser.add_argument(
        "--ch11-total-debt",
        type=float,
        default=None,
        help="Total debt for Ch. 11 feasibility",
    )
    parser.add_argument(
        "--ch11-tangible-pct",
        type=float,
        default=0.5,
        help="Tangible asset percentage (0.0-1.0, default 0.5) for liquidation value calculation",
    )
    
    # NEW: Expose hidden features
    parser.add_argument(
        "--adversarial-forensics",
        action="store_true",
        help="Run Adversarial Forensics analysis: Deep-dive into voting thresholds, amendment provisions, guarantor release triggers, and intercreditor gaps (Serta/Incora/J.Crew vectors)",
    )
    parser.add_argument(
        "--ica-file",
        type=str,
        default=None,
        help="Path to Intercreditor Agreement for adversarial forensics gap analysis",
    )
    parser.add_argument(
        "--priming-stress-test",
        action="store_true",
        help="Run priming stress test: compare pre/post-priming recovery scenarios (requires --waterfall or --from-signals)",
    )
    parser.add_argument(
        "--priming-amount",
        type=float,
        default=None,
        help="Priming facility amount for stress test (default: 30%% of senior debt)",
    )
    parser.add_argument(
        "--verify-evidence",
        action="store_true",
        help="Run Evidence Verifier: validate that all signals have source citations and evidence snippets",
    )

    args = parser.parse_args()

    # One-command pipeline: single file or batch
    if getattr(args, "pipeline", False):
        # Build forensic params if provided
        covenant_params = None
        if getattr(args, "covenant_headroom", False):
            covenant_ebitda = getattr(args, "covenant_ebitda", None)
            covenant_debt = getattr(args, "covenant_debt", None)
            covenant_max_lev = getattr(args, "covenant_max_leverage", None)
            if covenant_ebitda and covenant_debt and covenant_max_lev:
                addbacks_str = getattr(args, "covenant_addbacks", None)
                addbacks = {}
                if addbacks_str:
                    try:
                        addbacks = json.loads(addbacks_str)
                    except Exception:
                        print("Warning: Could not parse --covenant-addbacks JSON; using empty addbacks.", file=sys.stderr)
                covenant_params = {
                    "reported_ebitda": covenant_ebitda,
                    "addbacks": addbacks,
                    "total_debt": covenant_debt,
                    "leverage_covenant": covenant_max_lev,
                }
            else:
                print("Warning: --covenant-headroom requires --covenant-ebitda, --covenant-debt, --covenant-max-leverage.", file=sys.stderr)
        
        ch11_params = None
        if getattr(args, "ch11_feasibility", False):
            gc_ev = getattr(args, "ch11_gc_ev", None)
            secured = getattr(args, "ch11_secured_debt", None)
            total = getattr(args, "ch11_total_debt", None)
            if gc_ev and secured and total:
                tangible_pct = getattr(args, "ch11_tangible_pct", 0.5)
                ch11_params = {
                    "going_concern_ev": gc_ev,
                    "tangible_asset_pct": tangible_pct,
                    "secured_debt": secured,
                    "total_debt": total,
                }
            else:
                print("Warning: --ch11-feasibility requires --ch11-gc-ev, --ch11-secured-debt, --ch11-total-debt.", file=sys.stderr)
        
        if getattr(args, "batch", None):
            folder_path = Path(args.batch)
            if not folder_path.exists():
                print(f"Error: Batch folder not found: {folder_path}", file=sys.stderr)
                sys.exit(1)
            report = run_pipeline_batch(
                folder_path,
                recursive=getattr(args, "recursive", False),
                signals_path=getattr(args, "signals_path", "signals.json"),
                industry=getattr(args, "industry", None),
                geography=getattr(args, "geography", None),
                require_audit_gate=not getattr(args, "no_audit_gate", False),
                include_tornado=getattr(args, "tornado", False),
            )
            input_path = folder_path
            pipeline_mode = "batch"
        elif args.file:
            use_url = getattr(args, "url", False) or _is_url(args.file)
            use_edgar = getattr(args, "edgar", False) or (not use_url and _is_edgar_accession(args.file))
            cache_dir = getattr(args, "cache_dir", None)
            if use_url or use_edgar:
                report = run_pipeline(
                    args.file,
                    signals_path=getattr(args, "signals_path", "signals.json"),
                    industry=getattr(args, "industry", None),
                    geography=getattr(args, "geography", None),
                    require_audit_gate=not getattr(args, "no_audit_gate", False),
                    include_tornado=getattr(args, "tornado", False),
                    cache_dir=cache_dir,
                    covenant_params=covenant_params,
                    ch11_params=ch11_params,
                )
                input_path = args.file
            else:
                file_path = Path(args.file)
                if not file_path.exists() or not file_path.is_file():
                    print(f"Error: File not found: {file_path}", file=sys.stderr)
                    sys.exit(1)
                report = run_pipeline(
                    file_path,
                    signals_path=getattr(args, "signals_path", "signals.json"),
                    industry=getattr(args, "industry", None),
                    geography=getattr(args, "geography", None),
                    require_audit_gate=not getattr(args, "no_audit_gate", False),
                    include_tornado=getattr(args, "tornado", False),
                    cache_dir=cache_dir,
                    covenant_params=covenant_params,
                    ch11_params=ch11_params,
                )
                input_path = file_path
            pipeline_mode = "single"
        else:
            print("Error: --pipeline requires a file path or --batch FOLDER.", file=sys.stderr)
            sys.exit(1)
        out_path = getattr(args, "out", None)
        if out_path:
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=_json_default)
            manifest_path = write_run_manifest(
                out_path, report, pipeline_mode=pipeline_mode, input_path=input_path
            )
            print(f"Report written to {out_path}", file=sys.stderr)
            print(f"Run manifest written to {manifest_path}", file=sys.stderr)
        print(json.dumps(report, indent=2, default=_json_default))
        sys.exit(0 if report.get("published", True) else 1)

    if getattr(args, "benchmarker", False) and not args.waterfall:
        bench = run_benchmarker(
            industry=getattr(args, "industry", None),
            geography=getattr(args, "geography", None),
        )
        print(json.dumps(bench, indent=2))
        return 0

    if args.waterfall:
        tranches = None
        ev = args.ev
        if getattr(args, "from_signals", False):
            result_from_signals = run_waterfall_from_signals(
                getattr(args, "signals_path", "signals.json"),
                ev_override=ev,
            )
            if result_from_signals is not None:
                if ev is None:
                    ev = result_from_signals["ev_used"] + result_from_signals["ev_remaining"]
                tranches = [{"name": r["name"], "claim": r["claim"]} for r in result_from_signals["recoveries"]]
                result = result_from_signals
            else:
                result = None
        else:
            result = None
        if result is None:
            if ev is None:
                print("Error: --waterfall requires --ev (or --from-signals with signals.json containing default_ev).", file=sys.stderr)
                sys.exit(1)
            if not args.tranches:
                print("Error: --waterfall requires --tranches (or --from-signals with signals.json).", file=sys.stderr)
                sys.exit(1)
            tranches = _parse_tranches(args.tranches)
            result = run_waterfall(tranches, ev)
        if getattr(args, "sensitivity", False) and tranches is not None:
            base_ev = ev or (result["ev_used"] + result["ev_remaining"])
            sensitivity_results = ev_sensitivity(tranches, base_ev, ev_step=50.0, steps=5)
            if args.json:
                out = {"waterfall": result, "ev_sensitivity": [{"ev": s["ev"], "fulcrum": s["result"]["fulcrum_security"], "ev_used": s["result"]["ev_used"]} for s in sensitivity_results]}
                if getattr(args, "benchmarker", False):
                    model_recoveries = [{"name": r["name"], "recovery_pct": r["recovery_pct"]} for r in result["recoveries"]]
                    out["benchmarker"] = run_benchmarker(industry=getattr(args, "industry", None), geography=getattr(args, "geography", None), model_recoveries=model_recoveries)
                print(json.dumps(out, indent=2, default=_json_default))
            else:
                print("EV sensitivity (base_ev={}):".format(base_ev))
                for s in sensitivity_results:
                    print("  EV={}: fulcrum={}, ev_used={}".format(s["ev"], s["result"]["fulcrum_security"] or "N/A", s["result"]["ev_used"]))
            return 0
        if getattr(args, "tornado", False) and tranches is not None:
            base_ev = ev or (result["ev_used"] + result["ev_remaining"])
            collateral_adj = float(result.get("collateral_leakage_ev_adjustment", 0) or 0)
            tornado_results = tornado_drivers(tranches, base_ev, collateral_adjustment=collateral_adj)
            if args.json:
                out = {"waterfall": result, "tornado_drivers": tornado_results}
                if getattr(args, "benchmarker", False):
                    model_recoveries = [{"name": r["name"], "recovery_pct": r["recovery_pct"]} for r in result["recoveries"]]
                    out["benchmarker"] = run_benchmarker(industry=getattr(args, "industry", None), geography=getattr(args, "geography", None), model_recoveries=model_recoveries)
                print(json.dumps(out, indent=2, default=_json_default))
            else:
                print("Tornado drivers (base_ev={}, collateral_adj={}):".format(base_ev, collateral_adj))
                for d in tornado_results:
                    print("  {}: low={}, base={}, high={}".format(d["driver"], d["low"], d["base"], d["high"]))
                    for t in d["recovery_by_tranche"]:
                        print("    {}: low={}% base={}% high={}%".format(t["name"], t["low"], t["base"], t["high"]))
            return 0
        if getattr(args, "benchmarker", False):
            model_recoveries = [
                {"name": r["name"], "recovery_pct": r["recovery_pct"]}
                for r in result["recoveries"]
            ]
            bench = run_benchmarker(
                industry=getattr(args, "industry", None),
                geography=getattr(args, "geography", None),
                model_recoveries=model_recoveries,
            )
            result["benchmarker"] = bench
        if args.json:
            print(json.dumps(result, indent=2, default=_json_default))
        else:
            print("Recovery waterfall (EV={})".format(ev))
            for r in result["recoveries"]:
                print("  {}: claim={}, recovered={}, recovery_pct={}%".format(
                    r["name"], r["claim"], r["recovered"], r["recovery_pct"]))
            print("Fulcrum Security:", result["fulcrum_security"] or "N/A")
        return 0

    if args.batch:
        folder_path = Path(args.batch)
        if not folder_path.exists():
            print(f"Error: Batch folder not found: {folder_path}", file=sys.stderr)
            sys.exit(1)
        return _run_batch(
            folder_path,
            recursive=args.recursive,
            as_json=args.json,
            verbose=args.verbose,
            report_per_doc=getattr(args, "report_per_doc", False),
        )

    if not args.file:
        parser.print_help()
        print("\nError: Provide a file path to analyze, use --batch FOLDER, or use --waterfall with --ev and --tranches.", file=sys.stderr)
        sys.exit(1)

    # Check if file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.is_file():
        print(f"Error: '{args.file}' is not a file.", file=sys.stderr)
        sys.exit(1)

    # NEW: Adversarial Forensics: Deep-dive into exploitation vectors
    if getattr(args, "adversarial_forensics", False):
        try:
            chunks = read_document(file_path)
            credit_agreement_text = full_text(chunks)
            
            # Optional: Load Intercreditor Agreement
            ica_text = None
            ica_file = getattr(args, "ica_file", None)
            if ica_file:
                ica_path = Path(ica_file)
                if ica_path.exists() and ica_path.is_file():
                    ica_chunks = read_document(ica_path)
                    ica_text = full_text(ica_chunks)
                else:
                    print(f"Warning: ICA file '{ica_file}' not found. Proceeding without ICA analysis.", file=sys.stderr)
            
            # Run adversarial forensics
            report = perform_adversarial_forensics(credit_agreement_text, ica_text)
            
            # Output as JSON
            output = report.to_dict()
            output["file"] = str(file_path)
            if ica_file:
                output["ica_file"] = str(ica_file)
            
            print(json.dumps(output, indent=2))
            return 0
        except Exception as e:
            print(f"Error: Adversarial forensics failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # NEW: Priming Stress Test
    if getattr(args, "priming_stress_test", False):
        # Requires waterfall data (either --from-signals or --waterfall with --ev/--tranches)
        if not getattr(args, "from_signals", False) and not args.waterfall:
            print("Error: --priming-stress-test requires --from-signals or --waterfall.", file=sys.stderr)
            sys.exit(1)
        
        # Get tranches and EV
        tranches = None
        ev = args.ev
        if getattr(args, "from_signals", False):
            result_from_signals = run_waterfall_from_signals(
                getattr(args, "signals_path", "signals.json"),
                ev_override=ev,
            )
            if result_from_signals is not None:
                if ev is None:
                    ev = result_from_signals["ev_used"] + result_from_signals["ev_remaining"]
                tranches = [{"name": r["name"], "claim": r["claim"]} for r in result_from_signals["recoveries"]]
            else:
                print("Error: Could not load waterfall from signals.json", file=sys.stderr)
                sys.exit(1)
        else:
            if ev is None:
                print("Error: --priming-stress-test with --waterfall requires --ev", file=sys.stderr)
                sys.exit(1)
            if not args.tranches:
                print("Error: --priming-stress-test with --waterfall requires --tranches", file=sys.stderr)
                sys.exit(1)
            tranches = _parse_tranches(args.tranches)
        
        # Get priming amount
        priming_amount = getattr(args, "priming_amount", None)
        
        # Run priming stress test
        try:
            stress_result = run_priming_stress_test(
                tranches=tranches,
                ev=ev,
                priming_amount=priming_amount,
            )
            
            if args.json:
                print(json.dumps(stress_result, indent=2, default=_json_default))
            else:
                print(f"Priming Stress Test (EV={ev}, Priming={stress_result['priming_facility_amount']}):")
                print(f"  Fulcrum Migration: {stress_result['pre_priming']['fulcrum_security']} → {stress_result['post_priming']['fulcrum_security']}")
                print("  Recovery Changes:")
                for change in stress_result['recovery_changes']:
                    delta_pct = change['delta_recovery_pct']
                    sign = "+" if delta_pct > 0 else ""
                    print(f"    {change['name']}: {change['pre_recovery_pct']:.1f}% → {change['post_recovery_pct']:.1f}% ({sign}{delta_pct:.1f}%)")
            return 0
        except Exception as e:
            print(f"Error: Priming stress test failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # NEW: Evidence Verifier
    if getattr(args, "verify_evidence", False):
        try:
            # Load signals.json
            signals_path = Path(getattr(args, "signals_path", "signals.json"))
            if not signals_path.exists():
                print(f"Error: signals.json not found at {signals_path}. Run analysis first to generate signals.", file=sys.stderr)
                sys.exit(1)
            
            with open(signals_path, "r", encoding="utf-8") as f:
                signals_data = json.load(f)
            
            # Run evidence verifier
            verifier_result = run_evidence_verifier(signals_data)
            
            if args.json:
                print(json.dumps(verifier_result, indent=2))
            else:
                print("Evidence Verification Report:")
                print(f"  Total Signals: {verifier_result['total_signals']}")
                print(f"  Verified: {verifier_result['verified_signals']}")
                print(f"  Missing Evidence: {verifier_result['missing_evidence_count']}")
                print(f"  Pass: {'✅ YES' if verifier_result['pass'] else '❌ NO'}")
                if verifier_result['issues']:
                    print("  Issues:")
                    for issue in verifier_result['issues'][:10]:
                        print(f"    - {issue}")
                    if len(verifier_result['issues']) > 10:
                        print(f"    ... and {len(verifier_result['issues']) - 10} more")
            return 0
        except Exception as e:
            print(f"Error: Evidence verification failed: {e}", file=sys.stderr)
            sys.exit(1)

    # Distressed Librarian: extract Negative Covenants and Baskets, output JSON
    if getattr(args, "librarian", False):
        try:
            extraction = extract_baskets_and_covenants(path=file_path)
            out = extraction.to_dict()
            print(json.dumps(out, indent=2))
            return 0
        except ValueError as e:
            if "Unsupported format" in str(e):
                print(f"Error: Librarian supports .txt and .pdf only. {e}", file=sys.stderr)
            else:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Ingest via unified pipeline (text + PDF)
    try:
        chunks = read_document(file_path)
        text_content = full_text(chunks)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Page count for PDFs (for JSON/verbose)
    page_count = None
    if chunks and chunks[0].page_number is not None:
        page_count = len(chunks)

    # Librarian handoff: scan document, extract trap doors + LME, write signals.json for Quant
    try:
        signals_path = getattr(args, "signals_path", "signals.json")
        scan_document_and_write_signals(file_path, signals_path=signals_path)
    except Exception as e:
        if getattr(args, "verbose", False):
            print(f"Note: signals.json not updated ({e})", file=sys.stderr)
    
    # Calculate distress score and explanation
    result = analyze_text(text_content)
    score = result["score"]

    # JSON output for analyst workflows
    if args.json:
        output = {
            "file": str(file_path),
            "text_length": len(text_content),
            **result,
        }
        print(json.dumps(output, indent=2))
        return 0

    # Display results
    if args.verbose:
        print(f"File: {args.file}")
        print(f"Text length: {len(text_content)} characters")
        if page_count is not None:
            print(f"Pages: {page_count}")
        print(f"Distress Score: {score:.2f}")
        tier = result.get("tier", "unknown")
        tier_label = result.get("tier_label", "")
        if tier_label:
            print(f"Tier: {tier_label} ({tier})")
        else:
            print(f"Tier: {tier}")
        tier_thresholds = result.get("tier_thresholds", [])
        if tier_thresholds:
            thresh_str = ", ".join(
                "{} ({}-{})".format(t.get("name", ""), t.get("min", 0), t.get("max", 100))
                for t in tier_thresholds
            )
            print(f"Tier thresholds: {thresh_str}")
        breakdown = result.get("score_breakdown", {})
        if isinstance(breakdown, dict):
            comps = breakdown.get("components", [])
            if comps:
                print("Score breakdown (components):")
                for comp in comps:
                    name = comp.get("name", "")
                    contrib = comp.get("contribution", 0)
                    weight = comp.get("weight", 0)
                    conf = comp.get("confidence", 0)
                    print(f"  - {name}: contribution={contrib:.2f}, weight={weight:.1f}, confidence={conf:.2f}")
            sigs = breakdown.get("signals", [])
            if sigs:
                print("Score breakdown (signals):")
                for s in sigs:
                    ev = (s.get("evidence") or "")[:50]
                    if len(s.get("evidence") or "") > 50:
                        ev += "..."
                    print(f"  - [{s.get('type', '')}] weight={s.get('weight', 0)}, confidence={s.get('confidence', 0):.2f}: {ev}")
        else:
            for comp in result.get("score_breakdown", []):
                name = comp.get("name", "")
                contrib = comp.get("contribution", 0)
                weight = comp.get("weight", 0)
                conf = comp.get("confidence", 0)
                print(f"  - {name}: contribution={contrib:.2f}, weight={weight:.1f}, confidence={conf:.2f}")
        print("Explanation:")
        print(f"- Keyword matches: {result['keyword_count']}")
        if result["keywords_found"]:
            keywords_list = ", ".join(result["keywords_found"])
        else:
            keywords_list = "none"
        print(f"- Keywords found: {keywords_list}")
        print(f"- Keyword score contribution: {result['base_score']:.2f}")
        print(f"- Length score contribution: {result['length_factor']:.2f}")
        lme = result.get("lme_signals", [])
        if lme:
            print("LME signals:", len(lme))
            for s in lme[:5]:
                ev = (s.get("evidence") or "")[:60]
                if len(s.get("evidence") or "") > 60:
                    ev += "..."
                print(f"  - [{s.get('type', '')}] {s.get('label', '')}: {ev}")
        else:
            print("LME signals: none")
        checklist = result.get("analyst_checklist", [])
        if checklist:
            print("Analyst to-do:", len(checklist), "items")
            for i, item in enumerate(checklist[:10], 1):
                print("  {}. {}".format(i, item))
            if len(checklist) > 10:
                print("  ... and {} more".format(len(checklist) - 10))
        else:
            print("Analyst to-do: none")
    else:
        if getattr(args, "checklist_only", False):
            checklist = result.get("analyst_checklist", [])
            for item in checklist:
                print(item)
        else:
            print(f"{score:.2f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
