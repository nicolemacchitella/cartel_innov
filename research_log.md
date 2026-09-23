# Research Log — EU Cartels & Innovation

---

## Current state

- **Research question:** Does cartelisation raise or lower innovation in the affected industry × country market?
- **Where things stand:** `01_load`, `02_clean`, `03_panel` done. Estimation-ready panel `data/processed/panel.parquet` (163,680 rows, 34 cols; all restrictions as flags). No estimation attempted.
- **Next action:** Plan `04_estimate`: estimand (during vs after cartel), event-time support table, then estimator.
- **Open questions:**
  - Controls: participant vs non-participant cells (scope-only included) for initial estimates; clean-only (never exposed, never in scope) as check. Final choice after first estimates.
  - Estimand: absorbing `post` is 68% post-cartel years; separate during (year < `g_off`) and after.
  - Early onset (`left_cens` 34, `few_pre` 78 cells) and repeat episodes (`multi_ep` 37, `post_ep2` 806 rows): handling in 04.
  - `alp_artefact = ['360']` (4.5% of mass, never treated): confirm, robustness only.
Pipeline: `01_load` → `02_clean` → `03_panel` → `04_estimate`.

---

## Decisions

**Data and patents**
- **22/09/2026** — Patents: all EP applications from REGPAT (edition 202608); no family collapse. Country = applicant country.
- **22/09/2026** — Fractional counting: `app_share` × 1/n distinct IPC4 per application. EEA filter applied after the weights, no renormalisation (a DE–US co-application counts 0.5 for DE).
- **22/09/2026** — Industry: ISIC Rev.4 3-digit. Patents via ALP (IPC4 → ISIC3, probabilistic); post-2006 IPC subclasses mapped to predecessors; residual unmatched IPC4 dropped (ALP match 100.00% of mass).
- **22/09/2026** — ALP: current file = Version 2209 full; no release covers post-2006 IPC (built on IPC v8), so predecessor map kept. Switch to Version 2209 excluding services: 110 ISIC3 (sections A–F). Scope = goods-producing industries. (Treated counts: see 23/09.)
- **22/09/2026** — Outcomes: `pat_frac`, `cit3_frac`. Whole counts dropped.
- **22/09/2026** — IPC map from WIPO RCLs 2018–2027 (`scripts/ipc_map.py` → `ipc_new_to_old.csv`): 19 post-2006 subclasses mapped to ALP predecessors, shares = transferred groups. Weights split by share (G16H: G06F 0.5, G06Q 0.5). G16Y (no predecessor) and X99Z left unmatched. No other concordances needed; add RCL + inventory for each future IPC version and rerun.


**Cartels and treatment**
- **22/09/2026** — Panel countries: fixed 31 from `ref_ctry_timeline` (EU27 + GB + NO + IS + LI), all years. Non-EEA participants dropped (7 infringements lose treatment).
- **22/09/2026** — Treatment located by participating firms' country (`firms.ctry_iso`), not cartel scope. Associations count as treatment markers.
- **22/09/2026** — Industry mapping: NACE Rev.2 → ISIC4 by table lookup. All listed codes treated; 2-digit codes expand to the division, flagged `treat_2d` (27% of treated cell-years; robustness: set missing).
- **22/09/2026** — Timing: firm-level dates. `expo` = distinct cartelised days / days in year (overlapping participants counted once). Main: `treated = expo ≥ 0.5`; robustness: `expo > 0`.
- **22/09/2026** — All sectors kept; treated ISIC3 with no patents (453, 462, 502, 511) drop out.
- **23/09/2026** — Declared scope saved as scope_long.parquet (segment dates, year-level overlap; EU/EEA aggregates expanded to members by year; explicit lists literal; 1 infringements without scope).
- **23/09/2026** — Declared scope saved in 02 as `scope_long.parquet` (infringement × isic3 × ctry × year): segment dates, year-level overlap; EU/EEA aggregates expanded to members by year (entry year in, exit year out); explicit country lists literal; industry via `imap` (2-digit flagged). Full scope stored; subtraction of participants done in 03. 80/515 participant pairs outside declared scope: 44 treated cell-years pre-membership (CZ, ES, FI, HU, PL, SE), 195 participant home ≠ listed market. Kept treated.


**Panel (03)**
- **23/09/2026** — Grid: 110 ALP ISIC3 × 31 countries × 1978–2025, patents zero-filled. Documented drops only: priority years < 1978 (787 cell-years, mass 2,041.6, mostly partial 1977) and treated cells outside ALP ex-services (13 ISIC3, 55 cells, 311 treated cell-years; infringements 153 → 132). Remaining: 291 exposed cells, 290 treated, 2,854 treated cell-years, 46 treated ISIC3.
- **23/09/2026** — End cutoffs by rule (ref 2008–2019, first post-2019 year < mean − 3 SD): counts ≤ 2022 (`in_pat`; 2022 = 61.2k vs 53.9k), citations/patent ≤ 2020 (`in_cit`; 2021 = 0.311 vs 0.320, thin margin).
- **23/09/2026** — Start: country first year `t0` = max(1978, first EU/EEA entry) (`in_member`). Rationale: no EC jurisdiction before entry. EPC accession not used (restricts designation, not applicants). Exits not applied. 135 treated cell-years pre-membership.
- **23/09/2026** — Timing: episodes = spells of `expo > 0`. `g_on` (first `expo ≥ 0.5`, main cohort), `g_on_any` (first `expo > 0`), `g_off`, `g_ep2`, `g_dec` (earliest decision, episode 1), `n_ep`. Histories built on full `treat_cartel` before the 1978 cut. Flags: `left_cens` (onset < `t0`, 34 cells), `few_pre` (< 5 clean pre-years, 78), `multi_ep` (37), `post_ep2` (806 rows).
- **23/09/2026** — Controls as flags: `never_exp` (no exposure ever), `in_scope`, `scope_only` (in scope, no participant; 8,622 cell-years), `scope_ever`, `out_scope` (exposed, not in scope; 187), `isic_exposed` (same ISIC3 exposed elsewhere; 12.5% rows), `pat_zero_cell` (112 cells, none treated), `alp_artefact`. Clean controls: 322 cells; 6 treated ISIC3 have none (201, 383, 291, 210, 103, 252); 136/287 treated cells in ISIC3 with ≤ 1 clean control → clean-only check is effectively a subsample (national-cartel industries).
- **23/09/2026** — Comparison unit: ISIC3 × country cells hosting a participant vs cells without; treated cells pool participants and domestic rivals (not a firm-level comparison).
- **23/09/2026** — DiD variables: `cell_id`, `post` (absorbing, year ≥ `g_on`), `rel_time` (year − `g_on`, range −39 to 56). 6,073/8,927 `post = 1` rows are after episode 1 ends. Package-specific cohort coding, endpoint bins, episode and early-onset handling set in 04.

---

## Daily entries (newest at the top)

### 2026-09-23
**Did:** Added declared scope to `02_clean` (`scope_long.parquet`); fixed AT.29629_i1 scope; reran 02. Wrote and ran `03_panel`; added DiD variables.
**Found:** 02: 160 infringements, 1,219 EEA participants (153 infringements), 213 infringement × ISIC3 pairs, 346 cells, 3,655 exposed / 3,257 treated cell-years, 27.0% via 2-digit only. 75.3% of scope cell-years have no participant. 03: see Decisions 23/09.
**Problems:** EEA-wide cartels leave few clean controls within industry. Absorbing post-period mostly post-cartel. 27% of treated cells have < 5 clean pre-years (membership start). Citation cutoff margin thin.
**Next:** Plan 04.
 
### 2026-09-22
**Did:** Reviewed and ran `01_load` (fixed `applt_id` bug, dropped TPF collapse). Audited workbook; added `ctry_iso`, `participant_type`, `firm_exclude` to `firms`. Wrote and ran  `02_clean`. **Found:** Cartel: 158 infringements, 1,212 EEA participants, 59 ISIC3, 346 cells, 3,627 cell-years with expo > 0, 3,229 treated (27.2% via 2-digit only). Patents: 4.68M applications, 1.98M with an EEA applicant (41.8% of mass); ALP match 99.97%; 157,457 non-zero cell-years, 212 ISIC3, 31 countries. Outputs in `data/interim/`.
**Problems:** Counts fall after 2021, citations/patent after 2020 (truncation). EPO take-up drives growth 1978–1989. ALP assigns large mass to 592 and 360.
**Next:** Plan 03.

---

### To do

- [ ] 04_estimate: estimand (during/after), event-time support, estimator

---

## Meeting notes

### YYYY-MM-DD — with [who]
- Discussed:
- Agreed:
- To do (me):
- To do (them):

---

## Parking lot
 
- [ ] Inventor-country robustness (needs EPO_Inv in 01_load)
- [ ] Firm-level design using `firms` (participants vs rivals)
- [ ] Fine size as treatment intensity
- [ ] All-countries panel (non-EEA participants) as robustness
- [ ] Firms-only robustness (drops association-only AT.38279, AT.38238_i2, AT.34983)
- [ ] Van Looy IPC → NACE2 concordance as robustness
- [ ] Robustness flags: estimated dates, partial ISIC coverage (`treat_part`), multi-code infringements
- [ ] `n_cartels` as treatment intensity
- [ ] Modal-industry patent count (application → highest-weight ISIC3)
- [ ] Lifetime citations with truncation correction
- [ ] GB after EEA exit (2020)
- [ ] Scope-based (market-level) treatment with clean controls
- [ ] Participants outside declared scope (`out_scope`) as robustness
