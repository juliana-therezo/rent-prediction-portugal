"""Feature engineering.

Golden rule for a forecasting model: every feature in a row must be something I
would ALREADY KNOW at that row's quarter. The target is the rent 4 quarters later.
If a feature uses information from the future, the model "cheats" (data leakage)
and looks great in testing but fails in real life.
"""
import numpy as np

from src.config import FORECAST_HORIZON_QUARTERS

# NUTS III codes (2024 version) of the two metropolitan areas
AREA_BY_REGION_CODE = {
    "1A0": "Lisbon metro",   # Grande Lisboa
    "1B0": "Lisbon metro",   # Península de Setúbal
    "11A": "Porto metro",    # Área Metropolitana do Porto
}


def add_rent_history_features(panel):
    """Rent one year ago and rent growth over the last 12 months, for each municipality."""
    df = panel.copy()
    df["rent_lag_4q"] = df.groupby("municipality_code")["rent_m2"].shift(4)
    df["rent_growth_1y"] = df["rent_m2"] / df["rent_lag_4q"] - 1
    return df


def add_lease_activity_features(panel):
    """How big the long-term rental market is: number of new leases (log scale)."""
    df = panel.copy()
    df["log_new_leases"] = np.log1p(df["new_leases"])  # leases are very skewed (33 to 18,000)
    return df


def add_target(panel, horizon=FORECAST_HORIZON_QUARTERS):
    """Target = rent `horizon` quarters ahead. Negative shift = look into the future."""
    df = panel.copy()
    df["target_rent_next_year"] = df.groupby("municipality_code")["rent_m2"].shift(-horizon)
    df["target_growth_next_year"] = df["target_rent_next_year"] / df["rent_m2"] - 1
    return df


def add_population_features(panel, population):
    """Join the population of the PREVIOUS year (INE publishes year Y only in mid Y+1),
    and compute leases per 1,000 residents (how big the rental market is for its size).

    My population data starts in 2021, so 2020-2021 quarters use 2021 (small approximation,
    documented in the README).
    """
    df = panel.copy()
    df["population_year"] = (df["quarter"].dt.year - 1).clip(lower=population["year"].min())
    df = df.merge(population.rename(columns={"year": "population_year"}),
                  on=["municipality_code", "population_year"], how="left")
    df["log_population"] = np.log(df["population"])
    df["leases_per_1000"] = df["new_leases"] / df["population"] * 1000
    return df.drop(columns="population_year")


def add_location_features(panel):
    """Lisbon metro / Porto metro / rest of Portugal, built from the NUTS III region code."""
    df = panel.copy()
    df["area"] = df["region_code"].map(AREA_BY_REGION_CODE).fillna("Rest of Portugal")
    return df


def add_relative_features(panel):
    """Compare each municipality with the other municipalities of its NUTS III region, same quarter.

    'Is my rent cheap compared with my neighbours?' and 'is my rent growing faster than my
    neighbours?' The medians only use the same quarter, so no future information is used.
    """
    df = panel.copy()
    by_region_quarter = df.groupby(["region_code", "quarter"])
    df["rent_vs_region"] = df["rent_m2"] / by_region_quarter["rent_m2"].transform("median")
    df["growth_vs_region"] = df["rent_growth_1y"] - by_region_quarter["rent_growth_1y"].transform("median")
    return df


def build_model_dataset(panel, population):
    """Run every feature step in order."""
    df = add_rent_history_features(panel)
    df = add_lease_activity_features(df)
    df = add_target(df)
    df = add_population_features(df, population)
    df = add_location_features(df)
    df = add_relative_features(df)
    return df


def add_local_growth_target(df):
    """What the model learns: how much faster (+) or slower (-) a municipality's rent grows next
    year than the average of all municipalities in the same quarter."""
    df = df.copy()
    market_growth = df.groupby("quarter")["target_growth_next_year"].transform("mean")
    df["target_local_growth"] = df["target_growth_next_year"] - market_growth
    return df


def drop_unusable_rows(df, need_target=True):
    """Rows without current rent or rent 1 year ago cannot be used.
    For training I also need the target; for the final forecast I don't (it is the future)."""
    needed = ["rent_m2", "rent_lag_4q"] + (["target_rent_next_year"] if need_target else [])
    usable = df.dropna(subset=needed)
    print(f"kept {len(usable):,} of {len(df):,} rows "
          f"({usable['municipality_code'].nunique()} municipalities)")
    return usable.reset_index(drop=True)
