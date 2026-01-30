# Credit Integrity Report
## Adversarial Stress-Test — Recovery Engine & LME Parser

**Role:** Senior Distressed Debt Portfolio Manager / Credit Auditor  
**Scope:** `signal_triage/recovery_engine.py`, `signal_triage/lme_parser.py`  
**Mandate:** Trust nothing; precision audit; structural leakage check.

---

## Remediation status (post-audit)

| Section | Original result | Status |
|---------|-----------------|--------|
| **Math Check** | FAIL (float) | **Remediated:** `recovery_engine.py` uses `decimal.Decimal` for EV, claims, recovered; `ev_used + ev_remaining == ev` and `sum(recovered) == ev_used` in exact arithmetic. |
| **Seniority Enforcement** | FAIL (no Pari Passu) | **Remediated:** Tranches support optional `tier`/`priority`; same tier = Pari Passu (pro-rata by claim). See `run_waterfall` docstring and `test_pari_passu_pro_rata_recovery`. |
| **LME Vulnerability** | FAIL (missing patterns) | **Remediated:** `lme_parser.py` has `basket_transfer` (asset sale, investment basket, transfer to unrestricted subsidiary) and `structural_subordination`; tests in `test_lme_parser.py`. |

Re-run `python -m tests.credit_integrity_audit` after any further changes to verify.

---

## 1. Edge-Case Scenarios Executed

### Scenario 1: EV Drops Below 1st Lien Debt
- **Setup:** 1L = 500M, 2L = 200M, Unsecured = 300M; EV = 300M.
- **Expected:** 1L takes haircut (60% recovery); 2L and Unsecured 0%. Fulcrum = 1L.
- **Code behaviour:** Waterfall allocates 300M to 1L, 0 to 2L/Unsecured. Fulcrum correctly identified as 1L. **Logic Pass** for strict priority.
- **Risk:** If 1L and 2L were intended to be Pari Passu in an Intercreditor, this would misallocate (see Scenario 2).

### Scenario 2: 2nd Lien Claims Pari Passu Status (Intercreditor)
- **Setup:** 1L = 400M, 2L (Pari Passu with 1L) = 100M, Unsecured = 200M. EV = 400M.
- **Expected (Pari Passu 1L/2L):** 1L recovers 320M (80%), 2L recovers 80M (80%).
- **Code behaviour:** Strict order gives 1L 100% (400M), 2L 0%. **Seniority Fail.** The engine has no concept of shared priority; it allocates in list order only. A 2L with contractual Pari Passu through an Intercreditor Agreement would be incorrectly wiped.

### Scenario 3: Fulcrum at Boundary (EV = 1L Exactly) / Cramdown
- **Setup:** 1L = 250M, 2L = 150M; EV = 250M.
- **Expected:** 1L 100%, 2L 0%; Fulcrum = 2L (first tranche at 0%).
- **Code behaviour:** Correct. Fulcrum set to 2L per “first tranche at 0%” rule. **Pass.**

---

## 2. Math Check: **FAIL**

**Finding:** Recovery and EV arithmetic use native `float` and ad-hoc rounding. No `decimal.Decimal` or `math.fsum` anywhere.

| Location | Code | Issue |
|----------|------|--------|
| `recovery_engine.py` L34 | `remaining = float(ev)` | EV in millions represented as float; representation error accumulates. |
| `recovery_engine.py` L40–41 | `claim = float(t.get("claim", 0) or 0)` / `recovered = min(claim, remaining)` | Claims and recovered amounts in float; cascading rounding. |
| `recovery_engine.py` L44 | `remaining = max(0.0, remaining - recovered)` | Repeated subtraction of floats; residual “dust” in millions can be material. |
| `recovery_engine.py` L46 | `recovery_pct = (recovered / claim * 100.0)` | Float division and multiplication; not suitable for legal/recovery documentation. |
| `recovery_engine.py` L50 | `"recovery_pct": round(recovery_pct, 2)` | Rounding for display is acceptable only if underlying math is exact. |
| `recovery_engine.py` L59, 63–64 | `ev_used = ev - remaining` / `round(ev_used, 2)` / `round(remaining, 2)` | `ev_used` and `ev_remaining` can fail to sum to EV due to float + rounding. |

**Financial reason (Distressed-Grade risk):** In a Cramdown or plan allocation, recovery amounts are often in the tens or hundreds of millions. Float representation and repeated subtract/round can produce leakage (e.g. a few hundred dollars “missing” or double-counted). For auditability and legal defensibility, recovery calculations must use **Decimal** or **math.fsum** over exact decimal inputs so that totals reconcile to the penny.

**Remediation for Architect:** Use `decimal.Decimal` for `ev`, all `claim` and `recovered` values, and derive `recovery_pct` and display rounding from those. Alternatively, use cents/smallest currency unit as integers and convert only at output.

---

## 3. Seniority Enforcement: **FAIL** (Pari Passu / Structural)

**Finding:** The waterfall does not skip a tranche (it processes each in order), but it **does not enforce or model Pari Passu**. It assumes a strict sequential priority only.

| Location | Code | Issue |
|----------|------|--------|
| `recovery_engine.py` L37–57 | Single loop over `tranches`; `recovered = min(claim, remaining)`; `remaining -= recovered` | Treats order as strict priority. No grouping of “same priority” tranches for pro-rata allocation. |

**Financial reason:** In many structures, 1L and 2L (or multiple facilities) rank **Pari Passu** within a tier per the Intercreditor Agreement. Allocating strictly in list order can:
- Over-allocate to the first-listed tranche and wipe the other (Scenario 2).
- Misidentify the **Fulcrum security** (first loss-taking tranche), leading to wrong valuation and plan treatment.

**J.Crew / Structural:** The codebase does not model a “J.Crew blocker” (restriction on moving assets to an Unrestricted Subsidiary). That is a **covenant/document** concept, not a recovery math concept; the recovery engine does not ingest covenants. The **LME parser** does include “j.crew” and “unrestricted subsidiary” as dropdown phrases (`lme_parser.py` L13) but does not **enforce** or **flag** that a given recovery run is contingent on such covenants. So: document-level LME detection exists; recovery logic does not “see” blockers.

**Remediation for Architect:** (1) Extend `run_waterfall` to accept a **priority tier** (e.g. `priority: int` or `tier`) per tranche. For tranches in the same tier, allocate **pro-rata** by claim before moving to the next tier. (2) Document that list order implies strict priority unless tier is specified; do not assume Pari Passu without explicit tiering.

---

## 4. LME Vulnerability: **FAIL** (Basket Logic & Structural Language)

**Finding:** The LME scanner flags **phrase** matches only. It does not contain **Asset Sale** or **Investment** basket logic, and it does not explicitly flag **Unrestricted Subsidiary *transfers*** (only the phrase “unrestricted subsidiary”). **Structural subordination** language is not in the pattern set.

| Location | Code / Pattern Set | Issue |
|----------|--------------------|--------|
| `lme_parser.py` L10–24 | `LME_PATTERNS` | No phrase containing “asset sale”, “sale proceeds”, “asset sale basket”, or “investment basket”. |
| `lme_parser.py` L13 | `"unrestricted subsidiary"` in `dropdown` | Phrase “unrestricted subsidiary” is detected; “transfer to unrestricted subsidiary” or “sale to unrestricted sub” are not explicitly modelled — only substring match on “unrestricted subsidiary”. So **transfers** are not specifically flagged as a distinct risk. |
| `lme_parser.py` L19–23 | `uptiering` / `sprime_leakage` | No “structural subordination” or “structurally subordinated”. Scanner can **miss** disclosure that notes are structurally subordinated to secured debt. |

**Financial reason (Distressed-Grade risk):**  
- **Asset Sale / Investment baskets:** Covenant leakage often occurs through **basket** usage (e.g. asset sale proceeds to unrestricted subsidiary, or investments in unrestricted subs). If the scanner does not flag “asset sale” or “investment” basket language, an auditor may miss **Structural Leakage** that directly impacts collateral and recovery.  
- **Unrestricted Subsidiary transfers:** Merely detecting the phrase “unrestricted subsidiary” is insufficient; the **transfer** or **disposal** of value to an unrestricted sub is the event that impairs secured creditors. Mark as **High Risk Failure** until basket/transfer logic exists.  
- **Structural subordination:** Missing “structural subordination” leaves **LME Vulnerability** for noteholders; the scanner under-reports risk for unsecured or subordinated notes.

**Remediation for Architect:** (1) Add to `LME_PATTERNS` (or equivalent): **asset sale**, **asset sale proceeds**, **investment basket**, **restricted payment**, **transfer to unrestricted subsidiary**, **structural subordination**, **structurally subordinated**. (2) Consider a separate category for “basket / transfer” so that Unrestricted Subsidiary **transfers** are explicitly flagged, not only the phrase “unrestricted subsidiary”.

---

## 5. Summary Table

| Section | Result | Severity |
|---------|--------|----------|
| **Math Check** | **FAIL** | High — use Decimal/math.fsum for recovery and EV. |
| **Seniority Enforcement** | **FAIL** | High — Pari Passu not modelled; wrong allocation and fulcrum risk. |
| **LME Vulnerability** | **FAIL** | High — No Asset Sale/Investment basket logic; no explicit Unrestricted Subsidiary *transfer* or structural subordination. |

---

## 6. Remediation Checklist for Architect Agent

1. **recovery_engine.py**
   - Replace all recovery/EV arithmetic with `decimal.Decimal` (or integer cents + fsum). No raw `float` for claim/recovered/ev.
   - Add optional **priority tier** (or equivalent) to tranches; implement pro-rata within same tier before moving to next.
   - Document: “Strict priority only unless tier specified; Pari Passu requires explicit tier.”

2. **lme_parser.py**
   - Add patterns (or new category): **asset sale**, **asset sale proceeds**, **investment basket**, **restricted payment**, **transfer to unrestricted subsidiary**, **structural subordination** / **structurally subordinated**.
   - Treat “Unrestricted Subsidiary **transfer**” as a distinct, high-severity signal where possible (e.g. “transfer” + “unrestricted subsidiary” in same clause).

3. **Tests**
   - Add test: EV and claims in millions with decimal expectations; assert `sum(recovered) == ev` and `ev_used + ev_remaining == ev` in exact arithmetic.
   - Add test: Two tranches same priority (Pari Passu), EV &lt; sum of claims; assert pro-rata recovery.
   - Add test: Document containing “asset sale proceeds to unrestricted subsidiary” and “investment basket” produces expected LME signals.

---

*Report generated pursuant to Adversarial Mandate. Re-run `python -m tests.credit_integrity_audit` after changes to verify.*
