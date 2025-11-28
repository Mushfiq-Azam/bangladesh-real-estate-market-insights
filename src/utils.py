import os
import pandas as pd

RAW_DIR = "data/raw/"
CLEAN_DIR = "data/cleaned/"

def ensure_dir(path):
    """Create folder if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def save_raw_data(df, filename):
    ensure_dir(RAW_DIR)
    df.to_csv(os.path.join(RAW_DIR, filename), index=False)
    print(f"Saved raw data → {RAW_DIR}{filename}")

def save_clean_data(df, filename):
    ensure_dir(CLEAN_DIR)
    df.to_csv(os.path.join(CLEAN_DIR, filename), index=False)
    print(f"Saved cleaned data → {CLEAN_DIR}{filename}")
