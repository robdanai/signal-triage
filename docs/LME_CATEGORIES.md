# LME & Distress Signal Categories — Definitions and Rationale

Single source of truth for liability management (LME), covenant, and distress signal categories: what each means, why it matters for credit and recovery, and how Signal Triage detects it.

---

## 1. Structural / Collateral Leakage

### 1.1 Dropdown (`dropdown`)

**Definition.** A *dropdown* (or *drop-down*) is the transfer of valuable assets—often intellectual property, brand, or key collateral—from entities that guarantee the credit facility (restricted subsidiaries) into entities that do not (unrestricted subsidiaries). Once in an unrestricted sub, those assets can be pledged to new debt (or sold) without sharing proceeds with existing lenders. The effect is *guarantee stripping* or *collateral leakage*: the same enterprise value supports less obligation to the original secured group.

**Why it matters.** Secured and guaranteed lenders rely on subsidiary guarantees and collateral for recovery. A dropdown reduces the pool of assets backing their claims and can prime or subordinate them indirectly. Precedents (e.g. *J.Crew*, *Chewy*) established that covenant language permitting designation of unrestricted subsidiaries and transfers into them creates material leakage risk.

**Detection.** Phrases such as *release of guarantees*, *subsidiary guarantee*, *restricted subsidiary*, *unrestricted subsidiary*, *guarantee release*, *dropdown*, *J.Crew*, *dividend stopper*, *restriction on upstream*.

**Severity.** High when coupled with transfer/sale language; medium when only definitions appear.

**Related.** `transfer_to_unrestricted_sub`, `basket_transfer`, `sprime_leakage`.

---

### 1.2 S-Prime / Collateral Leakage (`sprime_leakage`)

**Definition.** *S-Prime* (or *S-Prime leakage*) refers to situations where second-lien or other junior secured debt is *primed*—i.e. new liens rank ahead of existing secured creditors on the same collateral. More broadly, *collateral leakage* is any covenant or structural feature that allows value to leave the secured group (e.g. additional secured debt, asset transfers, or baskets that permit encumbering or moving collateral).

**Why it matters.** First-lien recovery depends on collateral coverage and lien priority. Priming or leakage dilutes that coverage and can shift recovery from existing lenders to new money or other stakeholders. In bankruptcy, *adequate protection* and *priming* (e.g. DIP) are the legal hooks; in documents, incremental/debt baskets and unrestricted-sub language create the risk.

**Detection.** *First lien*, *second lien*, *primed*, *priming*, *adequate protection*, *collateral*, *security interest*, *leakage*, *sprime*, *s-prime*.

**Severity.** High when priming or uncapped incremental language; medium when only lien/collateral definitions.

**Related.** `uptiering`, `dropdown`, `incremental_facility` (document_intel).

---

### 1.3 Uptiering (`uptiering`)

**Definition.** *Uptiering* is an amendment or exchange in which participating lenders consent to new debt that ranks *above* existing debt (superpriority, priming lien, or roll-up into a senior facility). Non-participating lenders are left in a junior position without their consent. Often implemented via *roll-up* (existing loan converted into the new senior facility) and can occur in or out of court (e.g. *Serta*-style uptier, or DIP/exit facility in Chapter 11).

**Why it matters.** Non-participating lenders suffer immediate structural subordination and lower recovery. The same collateral supports a larger or senior claim; recovery for the original group drops. Litigation risk is high (e.g. *required lender*, good faith, coercion).

**Detection.** *Uptier*, *uptiering*, *superpriority*, *roll-up*, *priming lien*, *dip*, *exit facility*, *debtor-in-possession*.

**Severity.** High.

**Related.** `sprime_leakage`, `lender_voting_squeeze`, `crossover_prepack`.

---

### 1.4 Texas Two-Step / Structural Merger (`texas_two_step`)

**Definition.** The *Texas two-step* is a restructuring strategy that uses a *divisional* or *divisive* merger to separate liabilities from operating assets—often to isolate mass tort or other contingent claims in a separate entity that then files for bankruptcy, while the operating company continues. More generally, *two-step* or *LMT* (liability management transaction) structures can reshape legal entities to change which assets back which creditors.

**Why it matters.** Creditors of the operating company may find their claims or collateral tied to an entity that is deliberately separated from valuable operations. Liability separation can also be used in non-tort contexts to isolate debt in a subsidiary and leave parent or sister entities unencumbered.

**Detection.** *Texas two step*, *two-step*, *divisional merger*, *divisive merger*, *liability management transaction*, *LMT transaction*, *split-off*, *spin-off*, *divisional split*.

**Severity.** High when used to separate operating assets from creditor claims.

**Related.** `substantive_consolidation_cramdown`, `crossover_prepack`.

---

### 1.5 Double-Dip / Triple-Dip (`double_dip_triple_dip`)

**Definition.** A *double-dip* (or *triple-dip*) is a structure that creates *multiple claims on the same economic exposure*. Typically: (1) a loan to a *non-guarantor* or *empty-box* subsidiary, (2) an intercompany loan from that entity to a guarantor or borrower that already has debt, and (3) a parent or guarantor guarantee. The same dollar of value supports two (or three) claims at different levels of the capital structure, so participating creditors can recover more than 100% of their exposure in a default scenario. *Empty box* refers to a subsidiary with no material assets other than the intercompany claim.

**Why it matters.** Existing lenders share collateral and enterprise value with claims that did not exist when they lent. Recovery is diluted; non-participating lenders are structurally disadvantaged. Often used in conjunction with uptiers or consent solicitations.

**Detection.** *Double dip*, *triple dip*, *empty box*, *non-guarantor subsidiary*, *non-guarantor sub*, *multiple claims on same*, *intercompany loan*, *double recovery*.

**Severity.** High.

**Related.** `uptiering`, `consent_solicitation_exchange`, `structural_subordination`.

---

### 1.6 Basket / Transfer (`basket_transfer`)

**Definition.** Covenant *baskets* are exceptions that permit otherwise prohibited actions (e.g. asset sales, investments, restricted payments) up to a limit or under conditions. *Basket transfer* here means use of *asset sale*, *investment*, or *restricted payment* baskets to move value—especially *to unrestricted subsidiaries*—so that proceeds or assets leave the secured group. This is the mechanical path for many dropdowns and J.Crew-style moves.

**Why it matters.** Baskets define how much leakage is contractually allowed. Large or uncapped baskets, or baskets that permit transfers to unrestricted subs without sweep, create material leakage risk.

**Detection.** *Asset sale*, *asset sale proceeds*, *asset sale basket*, *investment basket*, *restricted payment*, *transfer to unrestricted subsidiary*, *sale to unrestricted subsidiary*, *proceeds to unrestricted subsidiary*.

**Severity.** Medium to high depending on caps and sweep language.

**Related.** `asset_sale`, `investment_basket`, `transfer_to_unrestricted_sub`, `dropdown`.

---

### 1.7 Asset Sale (`asset_sale`)

**Definition.** *Asset sale* here denotes covenant and document language governing dispositions of assets: permitted baskets, mandatory prepayment (sweep) of proceeds, and use of proceeds (e.g. reinvestment, paydown, or leakage to unrestricted subs). Distinct from the generic business term—we care about the *covenant* treatment.

**Why it matters.** Asset sale proceeds are a key source of paydown for secured lenders. Weak sweep (e.g. 50% vs 100%) or broad reinvestment/leakage baskets reduce expected recovery and can enable structural leakage.

**Detection.** *Asset sale*, *asset sale proceeds*, *asset sale basket*, *sale proceeds*, *asset sale covenant*.

**Severity.** Medium; escalates with weak sweep or unrestricted-sub leakage.

**Related.** `basket_transfer`, `transfer_to_unrestricted_sub`.

---

### 1.8 Investment Basket (`investment_basket`)

**Definition.** The *investment basket* is a covenant exception that permits the borrower and restricted subsidiaries to make investments (including in unrestricted subsidiaries) up to a dollar cap or formula. Capacity and *usage* of the basket determine how much value can be invested outside the secured group (e.g. in unrestricted subs or joint ventures).

**Why it matters.** Investments in unrestricted subsidiaries or in assets that are not collateral for the facility effectively transfer value out of the secured group. Large or fungible investment baskets are a standard leakage path.

**Detection.** *Investment basket*, *investment basket capacity*, *investment basket usage*, *permitted investment basket*.

**Severity.** Medium to high depending on size and whether investments can be in unrestricted subs.

**Related.** `basket_transfer`, `transfer_to_unrestricted_sub`, `dropdown`.

---

### 1.9 Transfer to Unrestricted Subsidiary (`transfer_to_unrestricted_sub`)

**Definition.** Explicit *transfer* or *sale* of assets (or proceeds) *to* an unrestricted subsidiary. This is the operational step in a J.Crew-style move: IP or other value is moved into an entity that is not a guarantor and can pledge assets to new lenders.

**Why it matters.** Directly reduces collateral and guarantee coverage for existing lenders. Often enabled by asset sale or investment baskets; the presence of explicit transfer language indicates the structure is contemplated in the documents.

**Detection.** *Transfer to unrestricted subsidiary*, *sale to unrestricted subsidiary*, *transfer to unrestricted sub*, *sale to unrestricted sub*, *proceeds to unrestricted subsidiary*.

**Severity.** High.

**Related.** `dropdown`, `basket_transfer`, `asset_sale`, `investment_basket`.

---

### 1.10 Structural Subordination (`structural_subordination`)

**Definition.** *Structural subordination* means that a claim (e.g. unsecured notes) ranks behind other claims not by contract (e.g. subordination agreement) but by *structure*: the notes are issued by a parent or holdco that has no assets other than equity in operating subsidiaries, and those subsidiaries have their own secured debt. In default, subsidiary assets go to subsidiary creditors first; noteholders get only what is left after subsidiary debt. So they are *structurally* subordinated to secured debt at the opco level.

**Why it matters.** Noteholders and other structurally subordinated creditors recover only after secured and subsidiary-level debt. Recovery is more volatile and typically lower than for secured lenders; LMEs that add secured or guaranteed debt at the opco level worsen structural subordination.

**Detection.** *Structural subordination*, *structurally subordinated*, *structurally subordinate*, *structural subordination of notes*, *notes structurally subordinated*.

**Severity.** High for noteholders; informs recovery tiering in the waterfall.

**Related.** `sprime_leakage`, `uptiering`, `double_dip_triple_dip`.

---

## 2. Out-of-Court LME & Process

### 2.1 Consent Solicitation / Exchange / Tender (`consent_solicitation_exchange`)

**Definition.** *Consent solicitation*: bondholders or lenders are asked to consent to an amendment (e.g. covenant strip, maturity extension, collateral release) often in exchange for a *consent payment*. *Exchange offer*: holders exchange existing debt for new debt (or mix of debt and equity) with different terms. *Tender offer*: debt is repurchased for cash. *Amend-and-extend* (A&E): amendments (e.g. maturity, covenants) in return for extension. These are the primary *out-of-court* LME tools.

**Why it matters.** They can change economics and priority without bankruptcy. Non-participating holders may be left with worse terms, shorter maturity, or subordinated claims. Consent thresholds (e.g. majority vs supermajority) and consent payments drive take-up and litigation risk.

**Detection.** *Consent solicitation*, *consent payment*, *exchange offer*, *tender offer*, *solicitation of consents*, *amend and extend*, *amend & extend*, *out-of-court restructuring*.

**Severity.** Medium to high depending on amendment scope and consent threshold.

**Related.** `uptiering`, `lender_voting_squeeze`, `forbearance_standstill`.

---

### 2.2 Equity Cure (`equity_cure`)

**Definition.** *Equity cure* (or *covenant cure*) is a right for the borrower (or sponsor) to inject *equity* or *equity-like* contribution to cure a covenant breach (e.g. bring a financial ratio back into compliance) and avoid default. Often limited by frequency (e.g. twice in life of facility) and/or dollar cap.

**Why it matters.** It extends runway and can prevent acceleration, but overuse signals ongoing covenant pressure. Caps and frequency limit how much “air” management has; uncapped or frequent cures can mask deterioration.

**Detection.** *Equity cure*, *equity injection*, *covenant cure*, *equity contribution*, *cure right*, *equity cure right*, *cure by equity*.

**Severity.** Medium; high if uncapped or very permissive.

**Related.** `liquidity_covenant`, `forbearance_standstill`.

---

### 2.3 Lender Voting Squeeze (`lender_voting_squeeze`)

**Definition.** Document mechanics that allow *majority* or *required* lenders to amend terms (e.g. maturity, covenants, collateral) *without* the consent of *non-consenting* or *out-of-the-money* lenders. *Yank-a-bank*: a lender can be replaced (bought out) so that consenting lenders reach the required threshold. *Snooze-you-lose*: lenders that do not respond by a deadline are deemed to consent. These features enable non-consensual uptiers and other LMEs.

**Why it matters.** Minority or holdout lenders can be structurally subordinated or diluted without consent. Recovery and control rights depend on whether the facility has these provisions and how high the consent bar is.

**Detection.** *Yank-a-bank*, *yank a bank*, *replaceable lender*, *required lender*, *majority lender*, *non-consenting lender*, *non-consenting*, *snooze you lose*, *snooze-you-lose*, *amendment without consent*, *out-of-the-money lenders*.

**Severity.** High when combined with uptier or priming language.

**Related.** `uptiering`, `consent_solicitation_exchange`.

---

### 2.4 Forbearance / Standstill (`forbearance_standstill`)

**Definition.** *Forbearance*: agreement by lenders not to exercise remedies (e.g. acceleration) for a period despite an existing default or breach. *Standstill*: agreement to refrain from taking specified actions (e.g. enforcing security, filing suit) for a defined period. Often used to buy time for a restructuring or sale.

**Why it matters.** Indicates existing or imminent default and that the borrower is in workout mode. Length and scope of forbearance/standstill affect runway and negotiating leverage.

**Detection.** *Forbearance*, *forbearance agreement*, *standstill*, *standstill agreement*, *forbearance period*, *waiver and forbearance*.

**Severity.** Medium to high (confirms distress).

**Related.** `potential_default`, `liquidity_covenant`, `crossover_prepack`.

---

## 3. Bankruptcy & Plan

### 3.1 Substantive Consolidation / Cramdown (`substantive_consolidation_cramdown`)

**Definition.** *Substantive consolidation*: bankruptcy doctrine that merges the assets and liabilities of related entities into a single estate for plan purposes, so that creditors of one entity may share in the assets of another. *Cramdown*: confirmation of a Chapter 11 plan over the objection of a class of creditors or equity, subject to *absolute priority* and *fair and equitable* requirements. *Plan confirmation* is the court order that binds all parties to the plan.

**Why it matters.** Substantive consolidation can reorder recovery (e.g. unsecured creditors of a weak entity may share in a strong entity’s assets). Cramdown determines whether holdouts can be bound and how value is allocated across classes.

**Detection.** *Substantive consolidation*, *substantively consolidated*, *cramdown*, *cram-down*, *cram down*, *absolute priority*, *fair and equitable*, *plan confirmation*.

**Severity.** High for recovery and plan risk.

**Related.** `texas_two_step`, `crossover_prepack`, `make_whole_disallowance`.

---

### 3.2 Crossover / Bridge / Prepack (`crossover_prepack`)

**Definition.** *Crossover facility*: financing that is intended to *cross over* from out-of-court into Chapter 11 (e.g. prepetition loan that becomes or rolls into DIP). *Bridge facility*: short-term financing to bridge to a longer-term solution or to bankruptcy. *Prepack* (prepackaged bankruptcy): plan terms are agreed with key creditors before filing; filing is used to implement the plan. *Plan support agreement* (PSA): agreement by certain creditors to support a plan (often in a prepack).

**Why it matters.** Indicates that a bankruptcy or restructuring path is contemplated or agreed. Crossover/bridge terms affect who funds the company in Ch. 11 and on what priority; prepack/PSA affect timing and recovery for consenting vs non-consenting creditors.

**Detection.** *Crossover facility*, *crossover financing*, *bridge facility*, *bridge financing*, *prepack*, *pre-pack*, *prepackaged*, *pre-arranged bankruptcy*, *prearranged*, *plan support agreement*.

**Severity.** High.

**Related.** `uptiering`, `substantive_consolidation_cramdown`, `forbearance_standstill`.

---

### 3.3 Make-Whole / Disallowance (`make_whole_disallowance`)

**Definition.** *Make-whole*: premium payable on early redemption or acceleration of debt (intended to compensate for lost interest). In bankruptcy, the question is whether the make-whole is *allowed* as a claim. *Disallowance*: Bankruptcy Code § 502(b) and case law limit *unmatured* (post-acceleration) interest and sometimes make-whole. *Claim disallowance* reduces the allowed claim and thus recovery for that creditor.

**Why it matters.** Make-whole can be a large component of a lender’s claim. Disallowance (e.g. *Townsend*) can significantly reduce recovery for secured and unsecured creditors.

**Detection.** *Make-whole*, *make whole*, *makewhole*, *disallowance*, *claim disallowance*, *unmatured interest*, *section 502(b)*.

**Severity.** High for creditors with make-whole or similar premium.

**Related.** `substantive_consolidation_cramdown`, `potential_default`.

---

## 4. Distress Indicators

### 4.1 Payment-in-Kind (PIK) (`pik`)

**Definition.** *Payment-in-kind* (PIK) interest: interest is not paid in cash but *added to principal* (or paid in additional notes). A *PIK toggle* gives the borrower the right to elect PIK instead of cash interest, often when covenant headroom is tight or the company is stressed.

**Why it matters.** PIK and PIK toggle are common in stressed and leveraged structures. Election of PIK signals liquidity or covenant pressure and increases leverage (debt grows with accrued PIK).

**Detection.** *Payment-in-kind*, *payment in kind*, *PIK interest*, *PIK toggle*, *PIK toggle right*, *pay-in-kind*, *pay in kind*.

**Severity.** Medium (distress indicator); high if PIK is mandatory or widely elected.

**Related.** `liquidity_covenant`, `debt_maturity_refinancing`, `equity_cure`.

---

## 5. Document-Intel-Only Categories (Trap Doors)

These are used by the Librarian (document_intel patterns) for covenant extraction; they may overlap with LME categories above or represent basket/covenant concepts that do not have a dedicated LME pattern.

| Category | Brief definition |
|----------|------------------|
| **asset_sale** | Asset sale covenant, baskets, sweep (see §1.7). |
| **unrestricted_subsidiary** | Designation and use of unrestricted subsidiaries (see §1.1, §1.9). |
| **incremental_facility** | Incremental debt capacity, free-and-clear basket, priming (see §1.2). |
| **affiliate_transaction** | Transactions with affiliates; dividends; management fees; arm’s length. |

---

## 6. Severity Summary

| Severity | Categories |
|----------|------------|
| **High** | dropdown, sprime_leakage, uptiering, texas_two_step, double_dip_triple_dip, transfer_to_unrestricted_sub, substantive_consolidation_cramdown, lender_voting_squeeze, crossover_prepack, make_whole_disallowance (when make-whole at risk), structural_subordination (for notes) |
| **Medium** | basket_transfer, asset_sale, investment_basket, consent_solicitation_exchange, equity_cure, forbearance_standstill, pik |
| **Context-dependent** | asset_sale / investment_basket (high if uncapped or leakage to unrestricted sub); equity_cure (high if uncapped). |

---

## 7. How Detection Works

- **LME parser** (`lme_parser.py`): Substring match on phrase lists per category; outputs signal type, label (matched phrase), evidence (snippet), span.
- **Document intel** (`document_intel/patterns.py`): Regex patterns over full text; used for trap-door extraction with section/page and dollar limits; feeds `collateral_leakage_flags` for Quant.
- **Signals config** (`signals_config.json`): Weights and phrase lists for distress scoring and reporting; LME categories that are also distress signals have entries here.
- **Checklist** (`checklist.py`): Per-category analyst to-do steps when a signal is present.

For full phrase and pattern lists, see `signal_triage/lme_parser.py` (LME_PATTERNS) and `signal_triage/document_intel/patterns.py`.
