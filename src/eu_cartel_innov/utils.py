import pandas as pd
from rapidfuzz import fuzz, process
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
tqdm.pandas()

def fuzzy_match(df1, df2, df1_col, df2_col, min_score=85, match_type='fuzzy', ctry_col=None):
    """
    Perform fuzzy matching between two datasets.

    Parameters:
    - df1: DataFrame 1 (source DataFrame)
    - df2: DataFrame 2 (target DataFrame)
    - df1_col: Column in df1 to match (e.g., 'firm_name')
    - df2_col: Column in df2 to match against (e.g., 'app_name')
    - threshold: Minimum fuzzy match score (default=85)
    - match_type: Type of match ('fuzzy') to label the matches (default='fuzzy')
    - ctry_col: Optional column in both DataFrames to filter by country (default=None)

    Returns:
    - DataFrame with matched values, similarity scores, and match type.
    """
    matched_values = []

    try: 
        # deduplicate dfs
        df1 = df1.drop_duplicates(subset=[df1_col], keep='first').copy()
        df2 = df2.drop_duplicates(subset=[df2_col], keep='first').copy()

        if ctry_col:
            # filter by country                    
            common_countries = set(df1[ctry_col]).intersection(df2[ctry_col])
            df1 = df1[df1[ctry_col].isin(common_countries)]
            df2 = df2[df2[ctry_col].isin(common_countries)]

        df2_list = df2[df2_col].tolist()

        print(f"total firms to match: {len(df1)} | unique lookup entries: {len(df2)}")

        # iterate over rows of the first DataFrame with a progress bar
        for _, df1_row in tqdm(df1.iterrows(), total=df1.shape[0], desc=f"matching {df1_col} to {df2_col}", unit="row"):
            value_to_match = df1_row[df1_col]

            try:
                # perform fuzzy matching
                best_match = process.extractOne(value_to_match, df2_list, scorer=fuzz.token_sort_ratio)

                if best_match and best_match[1] >= min_score:
                    matched_values.append({
                        f'{df1_col}': value_to_match,  
                        f'{df2_col}': best_match[0],  
                        'similarity_score': best_match[1],
                        'ctry_code': df1_row[ctry_col] if ctry_col else None,
                        'match_type': match_type
                    })
            except Exception as e:
                    print(f"error matching '{value_to_match}' in row {df1_row.name}: {e}")
                    continue  
    
        matched_df = pd.DataFrame(matched_values)
        
        print(f"matched {len(matched_df)}/{len(df1)} firms (Score >= {min_score})")
        print(f"match rate: {len(matched_df)/len(df1) * 100:.2f}%")

        return matched_df

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def fuzzy_match_parallel(df1, df2, df1_col, df2_col, min_score=85, match_type='fuzzy', ctry_col=None):
    matched_values = []

    try:
        # Deduplicate and filter by country if needed
        df1 = df1.drop_duplicates(subset=[df1_col], keep='first').copy()
        df2 = df2.drop_duplicates(subset=[df2_col], keep='first').copy()

        if ctry_col:
            common_countries = set(df1[ctry_col]).intersection(df2[ctry_col])
            df1 = df1[df1[ctry_col].isin(common_countries)]
            df2 = df2[df2[ctry_col].isin(common_countries)]

        df2_list = df2[df2_col].tolist()

        print(f"Total firms to match: {len(df1)} | Unique lookup entries: {len(df2)}")

        # Function to match a single row
        def match_row(df1_row, progress_bar):
            value_to_match = df1_row[df1_col]
            try:
                # Perform fuzzy matching with rapidfuzz
                best_match = process.extractOne(value_to_match, df2_list, scorer=fuzz.token_sort_ratio)

                if best_match and best_match[1] >= min_score:
                    return {
                        f'{df1_col}': value_to_match,
                        f'{df2_col}': best_match[0],
                        'similarity_score': best_match[1],
                        'ctry_code': df1_row[ctry_col] if ctry_col else None,
                        'match_type': match_type
                    }
                return None
            except Exception as e:
                print(f"Error matching '{value_to_match}' in row {df1_row.name}: {e}")
                return None
            finally:
                # Update the progress bar after the task completes
                progress_bar.update(1)

        # Use ThreadPoolExecutor to parallelize the row-wise matching
        with tqdm(total=len(df1), desc="Matching rows", unit="row") as progress_bar:
            with ThreadPoolExecutor() as executor:
                # Submit all tasks in parallel and pass the progress bar to each thread
                futures = [
                    executor.submit(match_row, row, progress_bar) for _, row in df1.iterrows()
                ]

                # Collect results as they finish
                for future in futures:
                    result = future.result()
                    if result:
                        matched_values.append(result)

        matched_df = pd.DataFrame(matched_values)

        # Now print the results after the progress bar has completed
        print(f"Matched {len(matched_df)}/{len(df1)} firms (Score >= {min_score})")
        print(f"Match rate: {len(matched_df)/len(df1) * 100:.2f}%")

        return matched_df

    except Exception as e:
        print(f"An unexpected error occurred: {e}")