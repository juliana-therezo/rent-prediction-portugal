"""Day 2 - Data cleaning.

Every INE table mixes the country, regions, municipalities and parishes in one list.
I keep the 278 municipalities of Portugal (the Azores and Madeira are not part of this
project) and join every source on the 4-digit municipality code, never on names
(names have accents and spelling differences).

Municipality code rules (INE geocod, 7 characters, e.g. '11A1317' = Vila Nova de Gaia):
- the first character is '1' for the municipalities in scope ('2' = Azores, '3' = Madeira),
- the first 3 characters are the NUTS III region ('11A' = Porto metropolitan area),
- the last 4 are the municipality code ('1317').
"""
import pandas as pd

QUARTER_WORDS = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4}


def keep_municipalities(df):
    """Municipality rows have a 7-character geocod; the ones in scope start with '1'."""
    is_municipality = df["geocod"].str.len() == 7
    is_in_scope = df["geocod"].str.startswith("1")  # excludes the Azores ('2') and Madeira ('3')
    return df[is_municipality & is_in_scope].copy()


def parse_quarter(label):
    """Turn INE's '3rd Quarter 2024' into a pandas Period('2024Q3')."""
    quarter_word, _, year = label.split()
    return pd.Period(year=int(year), quarter=QUARTER_WORDS[quarter_word], freq="Q")


def clean_quarterly_indicator(raw_df, value_name):
    """Clean one quarterly INE table -> municipality_code, municipality, region_code, quarter, value.

    INE marks suppressed values (too few contracts to publish a median) with
    sinal_conv = '-' and no 'valor'. pd.to_numeric(errors='coerce') turns them into NaN.
    """
    df = keep_municipalities(raw_df)
    df[value_name] = pd.to_numeric(df["valor"], errors="coerce")
    df["municipality_code"] = df["geocod"].str[-4:]
    df["region_code"] = df["geocod"].str[:3]
    df["quarter"] = df["period"].apply(parse_quarter)
    df = df.rename(columns={"geodsg": "municipality"})
    return df[["municipality_code", "municipality", "region_code", "quarter", value_name]]


def clean_population(raw_df):
    """One row per municipality and year: total population and age-structure shares."""
    df = keep_municipalities(raw_df)
    df = df[df["dim_3_t"] == "MF"]  # both sexes together
    df["value"] = pd.to_numeric(df["valor"], errors="coerce")
    df["municipality_code"] = df["geocod"].str[-4:]
    df["year"] = df["period"].astype(int)

    # Long -> wide: one column per age group
    wide = df.pivot_table(index=["municipality_code", "year"], columns="dim_4_t",
                          values="value", aggfunc="sum").reset_index()
    wide["population"] = wide["Total"]
    wide["share_age_25_64"] = wide["25 - 64 years"] / wide["Total"]
    wide["share_age_65_plus"] = wide["65 and more years"] / wide["Total"]
    wide.columns.name = None
    return wide[["municipality_code", "year", "population", "share_age_25_64", "share_age_65_plus"]]


def build_panel(rent, leases):
    """Combine rent and leases into a complete municipality x quarter grid.

    Why a complete grid? Later I use .shift(4) to look 4 quarters back/forward.
    That only works if every municipality has a row for EVERY quarter, even when
    the value is missing - otherwise shift(4) could silently jump 5 or 6 quarters.
    """
    municipalities = rent[["municipality_code", "municipality", "region_code"]].drop_duplicates()
    quarters = pd.period_range(rent["quarter"].min(), rent["quarter"].max(), freq="Q")
    grid = municipalities.merge(pd.DataFrame({"quarter": quarters}), how="cross")

    panel = (grid
             .merge(rent.drop(columns=["municipality", "region_code"]),
                    on=["municipality_code", "quarter"], how="left")
             .merge(leases.drop(columns=["municipality", "region_code"]),
                    on=["municipality_code", "quarter"], how="left"))
    return panel.sort_values(["municipality_code", "quarter"]).reset_index(drop=True)


def quick_check(df, name):
    """Print shape, duplicates and missing values - a quick health check after each step."""
    missing = df.isna().sum()
    print(f"--- {name} ---")
    print("rows, columns:", df.shape, "| duplicated rows:", df.duplicated().sum())
    print("missing values:", missing[missing > 0].to_dict() or "none")


def region_names(raw_df):
    """NUTS III region code -> name (INE lists regions as 3-character geocods, e.g. '11A')."""
    regions = raw_df[raw_df["geocod"].str.len() == 3][["geocod", "geodsg"]].drop_duplicates("geocod")
    return dict(zip(regions["geocod"], regions["geodsg"]))
