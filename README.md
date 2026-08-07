# EU Cartels & Innovation

Causal effect of cartel participation on innovation, using European Commission Article 101 TFEU prosecutions as the identification strategy. Treatment timing varies across industries; outcomes are patenting (EPO/REGPAT). Estimation uses heterogeneity-robust staggered DiD.

**Design.** Industry × country × year aggregate design at the **ISIC3 grain** (NACE 3-digit group).

## Data (not included)

None of `data/` is tracked. Sources are licensed and must be obtained separately:

| Source | Use | Licence |
|---|---|---|
| EU Commission cartel decisions | Treatment (Art. 1 scope + dates) | Public |
| `cartel_manual_v7.xlsx` (hand-built) | Normalized treatment dataset | This project |
| EPO / REGPAT | Patent outcomes | OECD licence |
| Orbis (Bureau van Dijk) | Firm controls | Licensed |


## Pipeline

Run order is `01 → 02 → 03`.

| # | File | Purpose | Status |
|---|---|---|---|
| — | `scripts/prep_cartel_seed.py` | Parse Commission search export → seed (superseded by the hand-maintained v7 workbook) | done |
| 01 | `01_load.ipynb` | Load raw EPO/PCT patents → `pat_data.parquet` | done |
| 02 | `02_clean.ipynb` | Cartel → treatment cells (`cartel_treated`); patents → ISIC3 industry panel (`pat_panel`) | done |
| 03 | `03_panel.ipynb` | Collapse to ISIC3 × country, build treatment vars (3 designs), assemble `panel.parquet` | done |
| 04 | `04_eda.ipynb` | Descriptives | planned |
| 05 | `05_results.ipynb` | Estimation | planned |


## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Method

Estimator: stacked DiD (headline); Callaway–Sant'Anna and de Chaisemartin–D'Haultfœuille as robustness. Inference: wild cluster bootstrap, two-way clustering (industry × country).

**Cohort not yet fixed.** Decision, formation, and breakup dates are carried as three parallel event-time designs (`evt_dec` / `evt_form` / `evt_brk`); the primary cohort is chosen at estimation from event-study pre-trends.

Close methodological parallel: Kang (2025).