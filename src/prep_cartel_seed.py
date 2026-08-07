#!/usr/bin/env python3
"""
prep_cartel_seed.py

Converts the raw European Commission case-search export
(`export_search-cartel_YYYY-MM-DD.xlsx`) into a tidy seed:
  - cartel_cleaned.xlsx   : one row per case (firms/NACE/legal-basis parsed to lists)
  - cartel_exploded.xlsx  : one row per (case, firm)

This is the seed that was subsequently hand-curated into the maintained
treatment workbook `data/raw/cartel/manual/cartel_manual_v7.xlsx`, which is
what the pipeline (02_clean.ipynb) reads directly. Nothing downstream reads
this script's output, it is kept only to record how the seed was produced.

Run manually if the raw export is ever refreshed:
    python scripts/prep_cartel_seed.py \
        --in  data/raw/export_search-cartel_2025-07-16_18-11.xlsx \
        --out data/interim
"""
import argparse
import re
from pathlib import Path

import pandas as pd

rename = {
    'Case number': 'cartel_id',
    'Case title': 'cartel_name',
    'Companies': 'firms_raw',
    'Economic activities': 'nace_raw',
}
nace_pattern = (
    r'(?P<nace_code>[A-Z]\.\d+(?:\.\d+)*) - '
    r'(?P<nace_name>.*?) \(NACE Rev\. (?P<nace_rev>\d+)\)'
)


def extract_firms(text):
    """split the companies cell into a clean list, dropping URL lines."""
    names = [line for line in str(text).split('\n') if not line.startswith('http')]
    return [name.strip() for name in names if name.strip()]


def extract_articles(text):
    """split a '+'-joined legal-basis string into a list of articles."""
    if pd.isna(text):
        return []
    return [a.strip() for a in str(text).split('+') if a.strip()]


def build(in_path: Path, out_dir: Path):
    df_raw = pd.read_excel(in_path)
    df = df_raw.rename(columns=rename)

    # firms
    df['firms_raw']  = df['firms_raw'].astype(str).str.strip()
    df['firms_list'] = df['firms_raw'].apply(extract_firms)

    # nace code / name / revision (one row may list several)
    matches = df['nace_raw'].str.extractall(nace_pattern)
    agg = matches.groupby(level=0).agg(list)
    df['nace_code'] = agg['nace_code']
    df['nace_name'] = agg['nace_name']
    df['nace_rev']  = agg['nace_rev']

    # legal basis
    df['Legal basis'] = df['Legal basis'].astype(str).str.strip()
    df['legal_basis'] = df['Legal basis'].apply(extract_articles)

    out_dir.mkdir(parents=True, exist_ok=True)

    cartel_cols = ['cartel_id', 'cartel_name', 'firms_list', 'nace_code',
                   'nace_name', 'nace_rev', 'legal_basis']
    df_cartel = df[cartel_cols]
    df_cartel.to_excel(out_dir / 'cartel_cleaned.xlsx', index=False)

    df_firms = (df[['cartel_id', 'cartel_name', 'firms_list']]
                .explode('firms_list')
                .rename(columns={'firms_list': 'firm'}))
    df_firms.to_excel(out_dir / 'cartel_exploded.xlsx', index=False)

    print(f'cases: {len(df_cartel)} | firm rows: {len(df_firms)}')
    print(f'wrote: {out_dir/"cartel_cleaned.xlsx"}, {out_dir/"cartel_exploded.xlsx"}')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--in', dest='in_path', type=Path,
                   default=Path('data/raw/export_search-cartel_2025-07-16_18-11.xlsx'))
    p.add_argument('--out', dest='out_dir', type=Path, default=Path('data/interim'))
    args = p.parse_args()
    build(args.in_path, args.out_dir)


if __name__ == '__main__':
    main()
