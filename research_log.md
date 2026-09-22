# Research Log — EU Cartels & Innovation

---

## Current state

- **Research question:** Does cartelisation raise or lower innovation in the affected industry × country market?
- **Where things stand:** `01_load` done (REGPAT EPO, edition 202608). Workbook `cartel_manual_v8.xlsx` updated (firm-level `ctry_iso`, `participant_type`, `firm_exclude`). `02_clean` rewritten and run: `treat_cartel.parquet`, `cartel_long.parquet`, `pat_isic3.parquet`. No estimation attempted.
- **Next action:** Review the IPC subclasses newer than ALP. Then plan `03_panel`.
- **Open questions:**
  - Sample cutoffs (proposed by criterion, confirm in 03): counts ≤ 2021, citations ≤ 2020; start 1978 + country EPC accession year.
  - Controls: ALP artefact industries (592, 360); scope-only countries (in declared cartel scope, no participant).
  - Repeat episodes (33 + 1 cells) and cells first treated before 1983 (19): handling in 03.
Pipeline: `01_load` → `02_clean` → `03_panel` → `04_estimate`.


---

## Decisions

**Data and patents**
- **22/09/2026** — Patents: all EP applications from REGPAT (edition 202608); no family collapse. Country = applicant country.
- **22/09/2026** — Fractional counting: `app_share` × 1/n distinct IPC4 per application. EEA filter applied after the weights, no renormalisation (a DE–US co-application counts 0.5 for DE).
- **22/09/2026** — Industry: ISIC Rev.4 3-digit. Patents via ALP (IPC4 → ISIC3, probabilistic); post-2018 IPC subclasses mapped to predecessors; residual unmatched IPC4 dropped (ALP match 99.97% of mass).
- **22/09/2026** — ALP: current file = Version 2209 full; no release covers post-2006 IPC (built on IPC v8), so predecessor map kept. Switch to Version 2209 excluding services (authors' recommendation): 110 ISIC3 (sections A–F). Treated: 46 ISIC3, 290 cells, 2,918 treated cell-years, 129 infringements. Scope = goods-producing industries.
- **22/09/2026** — Outcomes: `pat_frac`, `cit3_frac`. Whole counts dropped.
- **22/09/2026** — Sample cutoffs set in 03 by criterion.
- **22/09/2026** — IPC map from WIPO RCLs 2018–2027 (`scripts/ipc_map.py` → `ipc_new_to_old.csv`): 19 post-2006 subclasses mapped to ALP predecessors, shares = transferred groups. Weights split by share (G16H: G06F 0.5, G06Q 0.5). G16Y (no predecessor) and X99Z left unmatched. No other concordances needed; add RCL + inventory for each future IPC version and rerun.


**Cartels and treatment**
- **22/09/2026** — Panel countries: fixed 31 from `ref_ctry_timeline` (EU27 + GB + NO + IS + LI), all years. Non-EEA participants dropped (8 infringements lose treatment).
- **22/09/2026** — Treatment located by participating firms' country (`firms.ctry_iso`), not cartel scope. Associations count as treatment markers.
- **22/09/2026** — Industry mapping: NACE Rev.2 → ISIC4 by table lookup. All listed codes treated; 2-digit codes expand to the division, flagged `treat_2d` (27% of treated cell-years; robustness: set missing).
- **22/09/2026** — Timing: firm-level dates. `expo` = distinct cartelised days / days in year (overlapping participants counted once). Main: `treated = expo ≥ 0.5`; robustness: `expo > 0`.
- **22/09/2026** — All sectors kept; treated ISIC3 with no patents (453, 462, 502, 511) drop out.

---

## Daily entries (newest at the top)
 
### 2026-09-22
**Did:** Reviewed and ran `01_load` (fixed `applt_id` bug, dropped TPF collapse). Audited workbook; added `ctry_iso`, `participant_type`, `firm_exclude` to `firms`. Wrote and ran  `02_clean`. **Found:** Cartel: 158 infringements, 1,212 EEA participants, 59 ISIC3, 346 cells, 3,627 cell-years with expo > 0, 3,229 treated (27.2% via 2-digit only). Patents: 4.68M applications, 1.98M with an EEA applicant (41.8% of mass); ALP match 99.97%; 157,457 non-zero cell-years, 212 ISIC3, 31 countries. Outputs in `data/interim/`.
**Problems:** Counts fall after 2021, citations/patent after 2020 (truncation). EPO take-up drives growth 1978–1989. ALP assigns large mass to 592 and 360.
**Next:** Plan 03.

---

### To do

- [ ] 03_panel: patenting-industry threshold, merge, balance, event time
- [ ] 04_estimate

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
