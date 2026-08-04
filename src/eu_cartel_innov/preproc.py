import pandas as pd
import re
from unicodedata import category, normalize
from pathlib import Path

def replace_legal(series, remove=False):
    """replace or remove lagal terms in pandas series"""
    # load legal names dictionary
    csv_path = Path(__file__).parents[2] / 'data' / 'legal_names.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    legal_df = pd.read_csv(csv_path)
    # convert to dict
    legal_dict = legal_df.set_index('full_name')['abbreviation'].to_dict()
    # sort terms by length of full name (longest first)
    legal_pairs = sorted(legal_dict.items(), key=lambda x: len(x[0]), reverse=True)

    output = series.copy()
    # replace or remove terms
    for full, abbr in legal_pairs:
        if remove:
            output = output.str.replace(rf"\b{re.escape(full)}\b", "", case=False, regex=True)
            output = output.str.replace(rf"\b{re.escape(abbr)}\b", "", case=False, regex=True)
        else:
            output = output.str.replace(rf"\b{re.escape(full)}\b", abbr, case=False, regex=True)
    return output.str.replace(r"\s{2,}", " ", regex=True).str.strip()


def remove_punct(series, keep_spaces=True):
    """remove punctioation and optionally keep spaces"""
    if keep_spaces:
        pattern = r'[^\w&\s]'   # keep letters/digits/&/spaces
    else:
        pattern = r'[^\w&]'     # remove spaces too
    return series.str.replace(pattern,'', regex=True)


def unicode_to_ascii(text):
    """convert unicode text to ASCII safely"""
    text = normalize('NFD', text)
    transliteration_map = {
        'ä': 'a', 'à': 'a', 'á': 'a', 'ă': 'a', 'ą': 'a', 'ã': 'a', 'å': 'a', 
        'ā': 'a', 'ä': 'a', 'â': 'a', 'æ': 'ae', 'ß': 'ss', 'ć': 'c', 'č': 'c', 
        'ç': 'c', 'đ': 'd', 'ď': 'd', 'ê': 'e', 'ě': 'e', 'ë': 'e', 'ё': 'e', 
        'ė': 'e', 'è': 'e', 'ę': 'e', 'é': 'e', 'ƒ': 'f', 'ğ': 'g', 'ī': 'i', 
        'î': 'i', 'í': 'i', 'ï': 'i', 'ì': 'i', 'ļ': 'l', 'ń': 'n', 'ñ': 'n',
        'ö': 'o', 'õ': 'o', 'ò': 'o', 'ó': 'o', 'ô': 'o','œ': 'oe', 'ř': 'r',
        'ś': 's', 'ş': 's', 'š': 's', 'ţ': 't', 'ü': 'u', 'ů': 'u', 'ù': 'u', 
        'ú': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u', 'µ': 'u', 'ū': 'u', '×': 'x',
        'ý': 'y', 'ÿ': 'y', 'ż': 'z', 'ž': 'z',
    }
    text = ''.join(transliteration_map.get(c, c) for c in text if category(c) != 'Mn')
    return text.encode('ascii', 'ignore').decode()



def preproc(
    df: pd.DataFrame, 
    column_name: str, 
    lowercase: bool = True, 
    replace_legal_terms: bool = True,
    remove_legal_terms: bool = False, 
    keep_spaces: bool = True, 
    convert_ascii: bool = True
) -> pd.DataFrame:
    """ 
    Clean and normalize a DataFrame column (e.g., company names).
    
    Parameters:
    - df (pd.DataFrame): The dataframe to process.
    - column_name (str): The column to preprocess.
    - lowercase (bool): Whether to convert text to lowercase. Default is True.
    - replace_legal_terms (bool): Whether to replace legal terms. Default is True.
    - remove_legal_terms (bool): Whether to remove legal terms. Default is False.
    - keep_spaces (bool): Whether to keep spaces when removing punctuation. Default is True.
    - convert_ascii (bool): Whether to convert the text to ASCII. Default is True.

    Returns:
    - pd.DataFrame: The dataframe with the preprocessed column.
    """
    col_out = f"{column_name}_preproc"
    df[col_out] = df[column_name].astype(str)

    if lowercase:
        df[col_out] = df[col_out].str.lower()

    if replace_legal_terms:
        df[col_out] = replace_legal(df[col_out], remove=False)
    elif remove_legal_terms:
        df[col_out] = replace_legal(df[col_out], remove=True)

    df[col_out] = remove_punct(df[col_out], keep_spaces=keep_spaces)

    if convert_ascii:
        df[col_out] = df[col_out].apply(unicode_to_ascii)
   
    df[col_out] = df[col_out].str.replace(r"\s+", " ", regex=True).str.strip()
    return df


def bulk_preproc(
    df: pd.DataFrame, 
    column_name: str, 
    lowercase: bool = True, 
    replace_legal_terms: bool = True,
    remove_legal_terms: bool = False, 
    keep_spaces: bool = True, 
    convert_ascii: bool = True
) -> pd.DataFrame:
    """
    Bulk preprocess a large dataframe column by:
      1. Extracting unique values
      2. Preprocessing
      3. Mapping results back to the full df

    Parameters:
    - df_main (pd.DataFrame): The dataframe to process.
    - col_main (str): The column name to process.
    - lowercase (bool): Whether to convert text to lowercase. Default is True.
    - replace_legal_terms (bool): Whether to replace legal terms. Default is True.
    - remove_legal_terms (bool): Whether to remove legal terms. Default is False.
    - keep_spaces (bool): Whether to keep spaces. Default is True.
    - convert_ascii (bool): Whether to convert to ASCII. Default is True.

    Returns:
    - pd.DataFrame: The dataframe with a new column of preprocessed values.
    """
    df_unique = df[[column_name]].drop_duplicates(subset=[column_name], keep="first").copy()

    print(f"preprocessing {len(df_unique):,} unique values out of {len(df):,} total rows...")

    df_unique = preproc(df_unique, column_name, lowercase=lowercase, 
                           replace_legal_terms=replace_legal_terms, 
                           remove_legal_terms=remove_legal_terms, 
                           keep_spaces=keep_spaces, 
                           convert_ascii=convert_ascii)

    mapping = df_unique.set_index(column_name)[f'{column_name}_preproc'].to_dict()
    df[f"{column_name}_preproc"] = df[column_name].map(mapping)

    print(f"created column: '{column_name}_preproc'")
    
    return df
