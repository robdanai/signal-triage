"""
Basket Stacking Detection — Multi-Step Value Leakage Forensics.

Detects when multiple covenant baskets can be **stacked** to create larger leakage
paths than any individual basket allows. Example: Asset sale proceeds → investment
basket → transfer to unrestricted subsidiary = triple leakage.

Institutional Restructuring Desk: This is the "combinatorial trap door" analysis
that identifies when borrower can chain baskets to extract more value than appears
from reading any single covenant in isolation.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

QUANT = Decimal("0.01")


def _to_decimal(x: float | int | Decimal | str | None) -> Decimal:
    """Convert to Decimal, handling $ amounts and percentages."""
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, str):
        # Strip $ and M/MM/million
        x_clean = x.replace("$", "").replace(",", "").replace("M", "").replace("million", "").strip()
        try:
            return Decimal(x_clean)
        except Exception:
            return Decimal("0")
    return Decimal(str(x))


# Basket interaction graph: which baskets can flow into which
# Format: {source_category: [target_categories]}
BASKET_FLOW_GRAPH = {
    "asset_sale": ["investment_basket", "transfer_to_unrestricted_sub", "unrestricted_subsidiary"],
    "investment_basket": ["transfer_to_unrestricted_sub", "unrestricted_subsidiary"],
    "transfer_to_unrestricted_sub": ["unrestricted_subsidiary"],  # final destination
    "unrestricted_subsidiary": [],  # terminal: value has leaked out
}

# Stacking severity multipliers
STACKING_SEVERITY = {
    2: "medium",  # 2-step stack (e.g. asset sale → investment)
    3: "high",    # 3-step stack (e.g. asset sale → investment → unrestricted)
    4: "critical",  # 4+ step stack (rare but catastrophic)
}


def detect_basket_stacks(baskets: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Detect multi-step leakage paths where baskets can be stacked.

    A "stack" is a sequence of baskets where value can flow from one to the next:
    - Asset sale proceeds can be used in investment basket
    - Investment basket can fund transfer to unrestricted subsidiary
    - Unrestricted subsidiary is the final leak (value is out of secured group)

    Args:
        baskets: List of ExtractedBasket.to_dict() or similar with "category", "dollar_limit".

    Returns:
        Dict with stacks_detected (bool), stacking_paths (list of path dicts),
        max_stack_length (int), max_leakage_estimate (Decimal), stacking_severity (str).
    """
    if not baskets:
        return {
            "stacks_detected": False,
            "stacking_paths": [],
            "max_stack_length": 0,
            "max_leakage_estimate": Decimal("0"),
            "stacking_severity": "none",
        }

    # Build category presence and limits
    category_map: dict[str, list[dict]] = {}
    for b in baskets:
        cat = b.get("category", "")
        if cat not in category_map:
            category_map[cat] = []
        category_map[cat].append(b)

    # Find all stacking paths using BFS from each source basket
    stacking_paths = []
    
    def trace_path(start_cat: str, path: list[str]) -> list[list[str]]:
        """Recursively trace paths from start_cat; return all paths that reach a terminal or have len >= 2."""
        paths_found = []
        targets = BASKET_FLOW_GRAPH.get(start_cat, [])
        
        if not targets:
            # Terminal: if path length >= 2, it's a stack
            if len(path) >= 2:
                paths_found.append(path)
            return paths_found
        
        for target in targets:
            if target in category_map and target not in path:  # avoid cycles
                new_path = path + [target]
                # Recursively trace
                sub_paths = trace_path(target, new_path)
                paths_found.extend(sub_paths)
                # Also count this 2-step path even if it doesn't go further
                if len(new_path) >= 2:
                    paths_found.append(new_path)
        
        return paths_found
    
    # Trace from each source category
    for source_cat in ["asset_sale", "investment_basket", "transfer_to_unrestricted_sub"]:
        if source_cat in category_map:
            paths = trace_path(source_cat, [source_cat])
            for p in paths:
                # Get limits for each step
                limits = []
                for cat in p:
                    for b in category_map.get(cat, []):
                        lim = b.get("dollar_limit")
                        if lim:
                            limits.append(lim)
                            break  # just take first basket in category
                
                stacking_paths.append({
                    "path": p,
                    "stack_length": len(p),
                    "limits": limits,
                    "path_display": " → ".join(p),
                })
    
    # Deduplicate paths by path tuple
    seen_paths = set()
    unique_paths = []
    for sp in stacking_paths:
        key = tuple(sp["path"])
        if key not in seen_paths:
            seen_paths.add(key)
            unique_paths.append(sp)
    
    if not unique_paths:
        return {
            "stacks_detected": False,
            "stacking_paths": [],
            "max_stack_length": 0,
            "max_leakage_estimate": Decimal("0"),
            "stacking_severity": "none",
        }
    
    # Calculate max stack length and leakage estimate
    max_stack_length = max(sp["stack_length"] for sp in unique_paths)
    
    # Leakage estimate: sum of first limit in longest path (conservative)
    longest_path = max(unique_paths, key=lambda sp: sp["stack_length"])
    max_leakage_estimate = Decimal("0")
    if longest_path["limits"]:
        # Take first limit as proxy (they stack, so max leakage = smallest bottleneck, but for warning use first)
        max_leakage_estimate = _to_decimal(longest_path["limits"][0])
    
    # Severity
    severity = STACKING_SEVERITY.get(max_stack_length, "critical" if max_stack_length >= 4 else "medium")
    
    return {
        "stacks_detected": True,
        "stacking_paths": unique_paths,
        "max_stack_length": max_stack_length,
        "max_leakage_estimate": max_leakage_estimate.quantize(QUANT, rounding=ROUND_HALF_UP),
        "stacking_severity": severity,
        "note": f"{len(unique_paths)} leakage path(s) detected; max stack length {max_stack_length}; " +
                f"leakage estimate: {max_leakage_estimate.quantize(QUANT, rounding=ROUND_HALF_UP)}; " +
                f"severity: {severity.upper()}.",
    }


def analyze_basket_interactions(baskets: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Full basket interaction analysis: stacking + aggregate leakage exposure.

    Args:
        baskets: List of baskets from Librarian (ExtractedBasket.to_dict()).

    Returns:
        Dict with stacks_detected, stacking_paths, aggregate_leakage_capacity,
        high_risk_paths (length >= 3), forensic_note.
    """
    stacking = detect_basket_stacks(baskets)
    
    # Aggregate leakage capacity: sum of all dollar limits (upper bound)
    aggregate_leakage = Decimal("0")
    for b in baskets:
        lim = b.get("dollar_limit")
        if lim:
            aggregate_leakage += _to_decimal(lim)
    
    # High-risk paths: stack length >= 3 (triple leakage or more)
    high_risk_paths = [
        sp for sp in stacking.get("stacking_paths", [])
        if sp.get("stack_length", 0) >= 3
    ]
    
    forensic_note = ""
    if stacking["stacks_detected"]:
        forensic_note = (
            f"Basket stacking detected: {len(stacking['stacking_paths'])} path(s). "
            f"Longest path: {stacking['max_stack_length']} steps. "
            f"Max leakage estimate: {stacking['max_leakage_estimate']}. "
        )
        if high_risk_paths:
            forensic_note += f"HIGH RISK: {len(high_risk_paths)} path(s) with 3+ steps (triple leakage or more). "
        forensic_note += f"Aggregate leakage capacity (all baskets): {aggregate_leakage.quantize(QUANT, rounding=ROUND_HALF_UP)}."
    else:
        forensic_note = "No basket stacking detected; baskets do not appear to interact."
    
    return {
        "stacks_detected": stacking["stacks_detected"],
        "stacking_paths": stacking.get("stacking_paths", []),
        "max_stack_length": stacking.get("max_stack_length", 0),
        "max_leakage_estimate": stacking.get("max_leakage_estimate", Decimal("0")),
        "stacking_severity": stacking.get("stacking_severity", "none"),
        "aggregate_leakage_capacity": aggregate_leakage.quantize(QUANT, rounding=ROUND_HALF_UP),
        "high_risk_paths": high_risk_paths,
        "high_risk_path_count": len(high_risk_paths),
        "forensic_note": forensic_note,
    }
