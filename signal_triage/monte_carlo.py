"""
Monte Carlo Simulation Engine for Probabilistic Recovery Analysis

Generates 10,000+ scenarios with varying EBITDA, EV multiples, and collateral leakage
assumptions to produce probability distributions of recovery outcomes.

Used by Reporter for risk heatmaps showing "Likelihood of Par Recovery" under different
market conditions.
"""

import random
from decimal import Decimal
from typing import Any, Callable
from dataclasses import dataclass

from signal_triage.recovery_engine import run_waterfall, _to_decimal


@dataclass
class MonteCarloParams:
    """Parameters for Monte Carlo simulation."""
    
    # Number of simulation runs
    n_simulations: int = 10_000
    
    # EV distribution parameters (normal distribution)
    ev_mean: float = 150.0
    ev_std: float = 30.0  # Standard deviation
    ev_min: float = 50.0  # Floor
    ev_max: float = 300.0  # Ceiling
    
    # EBITDA multiple distribution (normal)
    multiple_mean: float = 8.0
    multiple_std: float = 2.0
    multiple_min: float = 4.0
    multiple_max: float = 15.0
    
    # Collateral leakage probability and severity
    leakage_probability: float = 0.3  # 30% chance of leakage
    leakage_mean_pct: float = 0.15  # Average 15% reduction when it occurs
    leakage_std_pct: float = 0.08  # Std dev of leakage
    
    # Random seed for reproducibility
    seed: int | None = None


@dataclass
class MonteCarloResult:
    """Results of Monte Carlo simulation."""
    
    # All simulation runs
    scenarios: list[dict[str, Any]]
    
    # Per-tranche statistics
    tranche_statistics: list[dict[str, Any]]
    
    # Probability distributions
    fulcrum_probabilities: dict[str, float]
    
    # Overall statistics
    params: MonteCarloParams
    n_runs: int


def run_monte_carlo(
    tranches: list[dict[str, Any]],
    params: MonteCarloParams | None = None,
    *,
    use_ebitda_multiple: bool = False,
    base_ebitda: float | None = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation for probabilistic recovery analysis.
    
    Args:
        tranches: Capital structure (name, claim, optional tier).
        params: Simulation parameters. If None, uses defaults.
        use_ebitda_multiple: If True, simulates EBITDA*Multiple instead of raw EV.
        base_ebitda: Required if use_ebitda_multiple is True.
    
    Returns:
        MonteCarloResult with scenarios, statistics, and probability distributions.
    """
    if params is None:
        params = MonteCarloParams()
    
    if params.seed is not None:
        random.seed(params.seed)
    
    if use_ebitda_multiple and base_ebitda is None:
        raise ValueError("base_ebitda required when use_ebitda_multiple=True")
    
    scenarios = []
    tranche_names = [t.get("name", f"Tranche {i}") for i, t in enumerate(tranches)]
    
    # Run simulations
    for run_id in range(params.n_simulations):
        # Sample EV or EBITDA multiple
        if use_ebitda_multiple:
            multiple = _sample_normal(
                params.multiple_mean,
                params.multiple_std,
                params.multiple_min,
                params.multiple_max,
            )
            ev = base_ebitda * multiple
        else:
            ev = _sample_normal(
                params.ev_mean,
                params.ev_std,
                params.ev_min,
                params.ev_max,
            )
        
        # Sample collateral leakage
        leakage_adjustment = 0.0
        leakage_occurred = False
        if random.random() < params.leakage_probability:
            leakage_occurred = True
            leakage_pct = _sample_normal(
                params.leakage_mean_pct,
                params.leakage_std_pct,
                0.0,
                0.5,  # Max 50% leakage
            )
            leakage_adjustment = ev * leakage_pct
        
        # Apply leakage
        ev_adjusted = max(0, ev - leakage_adjustment)
        
        # Run waterfall
        result = run_waterfall(tranches, ev_adjusted)
        
        # Extract recoveries
        recoveries = result.get("recoveries", [])
        fulcrum = result.get("fulcrum_security")
        
        scenario = {
            "run_id": run_id,
            "ev": ev,
            "ev_adjusted": ev_adjusted,
            "leakage_adjustment": leakage_adjustment,
            "leakage_occurred": leakage_occurred,
            "fulcrum_security": fulcrum,
            "recoveries": recoveries,
        }
        
        if use_ebitda_multiple:
            scenario["multiple"] = multiple
            scenario["ebitda"] = base_ebitda
        
        scenarios.append(scenario)
    
    # Calculate per-tranche statistics
    tranche_statistics = []
    for i, name in enumerate(tranche_names):
        recoveries_pct = []
        par_recovery_count = 0
        
        for scenario in scenarios:
            rec_list = scenario["recoveries"]
            if i < len(rec_list):
                rec_pct = float(rec_list[i].get("recovery_pct", 0))
                recoveries_pct.append(rec_pct)
                if rec_pct >= 100.0:
                    par_recovery_count += 1
        
        if recoveries_pct:
            recoveries_sorted = sorted(recoveries_pct)
            n = len(recoveries_sorted)
            
            stats = {
                "tranche": name,
                "mean_recovery": sum(recoveries_pct) / n,
                "median_recovery": recoveries_sorted[n // 2],
                "p10_recovery": recoveries_sorted[max(0, int(n * 0.1))],
                "p25_recovery": recoveries_sorted[max(0, int(n * 0.25))],
                "p75_recovery": recoveries_sorted[min(n - 1, int(n * 0.75))],
                "p90_recovery": recoveries_sorted[min(n - 1, int(n * 0.90))],
                "min_recovery": recoveries_sorted[0],
                "max_recovery": recoveries_sorted[-1],
                "par_probability": par_recovery_count / n,  # Probability of 100%+ recovery
                "impaired_probability": sum(1 for r in recoveries_pct if r < 100) / n,
                "zero_probability": sum(1 for r in recoveries_pct if r == 0) / n,
            }
            tranche_statistics.append(stats)
    
    # Calculate fulcrum probabilities
    fulcrum_counts: dict[str, int] = {}
    for scenario in scenarios:
        fulcrum = scenario.get("fulcrum_security")
        if fulcrum:
            fulcrum_counts[fulcrum] = fulcrum_counts.get(fulcrum, 0) + 1
    
    n_scenarios = len(scenarios)
    fulcrum_probabilities = {
        name: count / n_scenarios
        for name, count in fulcrum_counts.items()
    }
    
    return MonteCarloResult(
        scenarios=scenarios,
        tranche_statistics=tranche_statistics,
        fulcrum_probabilities=fulcrum_probabilities,
        params=params,
        n_runs=n_scenarios,
    )


def _sample_normal(
    mean: float,
    std: float,
    min_val: float,
    max_val: float,
) -> float:
    """Sample from normal distribution with clipping."""
    value = random.gauss(mean, std)
    return max(min_val, min(max_val, value))


def export_monte_carlo_summary(result: MonteCarloResult) -> dict[str, Any]:
    """
    Export Monte Carlo results as a JSON-serializable dict for dashboard/reports.
    
    Returns:
        Dict with tranche_statistics, fulcrum_probabilities, params.
    """
    return {
        "n_simulations": result.n_runs,
        "params": {
            "ev_mean": result.params.ev_mean,
            "ev_std": result.params.ev_std,
            "leakage_probability": result.params.leakage_probability,
            "leakage_mean_pct": result.params.leakage_mean_pct,
        },
        "tranche_statistics": result.tranche_statistics,
        "fulcrum_probabilities": result.fulcrum_probabilities,
    }


def generate_risk_heatmap_data(
    tranches: list[dict[str, Any]],
    ev_range: tuple[float, float] = (50, 300),
    leakage_range: tuple[float, float] = (0, 0.3),
    n_points: int = 20,
) -> list[dict[str, Any]]:
    """
    Generate data for a 2D risk heatmap (EV vs Collateral Leakage).
    
    For each (EV, leakage) grid point, compute recovery rates and return as list
    of dicts suitable for Plotly/Altair heatmap visualization.
    
    Args:
        tranches: Capital structure.
        ev_range: (min_ev, max_ev) for grid.
        leakage_range: (min_leakage_pct, max_leakage_pct) for grid.
        n_points: Number of grid points per dimension (total n_points^2 calculations).
    
    Returns:
        List of dicts with keys: ev, leakage_pct, tranche, recovery_pct.
    """
    ev_min, ev_max = ev_range
    leakage_min, leakage_max = leakage_range
    
    ev_step = (ev_max - ev_min) / (n_points - 1)
    leakage_step = (leakage_max - leakage_min) / (n_points - 1) if n_points > 1 else 0
    
    heatmap_data = []
    
    for i in range(n_points):
        ev = ev_min + i * ev_step
        
        for j in range(n_points):
            leakage_pct = leakage_min + j * leakage_step
            leakage_amount = ev * leakage_pct
            ev_adjusted = max(0, ev - leakage_amount)
            
            result = run_waterfall(tranches, ev_adjusted)
            recoveries = result.get("recoveries", [])
            
            for rec in recoveries:
                heatmap_data.append({
                    "ev": ev,
                    "leakage_pct": leakage_pct * 100,  # Convert to percentage
                    "tranche": rec.get("name", ""),
                    "recovery_pct": float(rec.get("recovery_pct", 0)),
                })
    
    return heatmap_data
