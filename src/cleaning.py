import pandas as pd
import re
from utils import save_clean_data

def clean_price(price_str):
    """Convert prices like 'Tk 1.2 Crore' or '45 lakh' → numeric."""
    if not isinstance(price_str, str):
        return None

    price_str = price_str.lower().replace(",", "")

    if "crore" in price_str:
        num = float(re.findall(r"[\d.]+", price_str)[0])
        return num * 10000000  # 1 crore = 10,000,000

    if "lakh" in price_str:
        num = float(re.findall(r"[\d.]+", price_str)[0])
        return num * 100000  # 1 lakh = 100,000

    match = re.findall(r"[\d.]+", price_str)
    return float(match[0]) if match else None

def extract_area(title):
    """Extract area from title (e.g. '1200 sqft')."""
    match = re.search(r"(\d{3,5})\s*(sqft|sft|ft)", title.lower())
    return int(match.group(1)) if match else None

def clean_dataset(path="data/raw/brokeragebd_raw.csv"):
    """Clean the raw data and save a structured dataset."""
    df = pd.read_csv(path)

    df["price_clean"] = df["price"].apply(clean_price)
    df["area_sqft"] = df["title"].apply(extract_area)

    df["location"] = df["location"].str.strip()

    df = df.drop_duplicates()
    df = df.dropna(subset=["price_clean"])

    save_clean_data(df, "brokeragebd_clean.csv")
    return df


if __name__ == "__main__":
    df = clean_dataset()
    print(df.head())
