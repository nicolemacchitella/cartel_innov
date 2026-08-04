from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from rapidfuzz import fuzz, process
import pandas as pd

def fuzzy_match_row(args):
    value_to_match, df2_list, df1_col, df2_col, min_score, match_type, ctry_value = args

    best_match = process.extractOne(value_to_match, df2_list, scorer=fuzz.token_sort_ratio)

    if best_match and best_match[1] >= min_score:
        return {
            df1_col: value_to_match,
            df2_col: best_match[0],
            "similarity_score": best_match[1],
            "ctry_code": ctry_value,
            "match_type": match_type
        }
    return None


def fuzzy_match(df1, df2, df1_col, df2_col, min_score=85, match_type='fuzzy', ctry_col=None):

    df1 = df1.drop_duplicates(subset=[df1_col]).copy()
    df2 = df2.drop_duplicates(subset=[df2_col]).copy()

    if ctry_col:
        common = set(df1[ctry_col]).intersection(df2[ctry_col])
        df1 = df1[df1[ctry_col].isin(common)]
        df2 = df2[df2[ctry_col].isin(common)]

    df2_list = df2[df2_col].tolist()

    tasks = []
    for row in df1.itertuples():
        value_to_match = getattr(row, df1_col)
        ctry_value = getattr(row, ctry_col) if ctry_col else None
        tasks.append((value_to_match, df2_list, df1_col, df2_col,
                      min_score, match_type, ctry_value))

    results = []

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(fuzzy_match_row, t) for t in tasks]

        for f in tqdm(as_completed(futures), total=len(futures), desc="Matching"):
            r = f.result()
            if r:
                results.append(r)

    return pd.DataFrame(results)
