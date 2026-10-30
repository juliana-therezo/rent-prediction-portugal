"""Day 1 - Data acquisition from the INE API (Statistics Portugal).

Three indicators: long-term rent, number of new long-term leases and population.
Each indicator is requested once with all periods and cached in data/raw/,
so later runs never call the API again.
"""
import json
import time

import pandas as pd
import requests

from src.config import INE_URL, RAW_DIR


def fetch_ine_indicator(indicator_code, use_cache=True, retries=3, timeout=180):
    """Return the INE JSON for one indicator (all periods), using a local cache file."""
    cache_file = RAW_DIR / f"ine_{indicator_code}_all.json"
    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    params = {"op": "2", "varcd": indicator_code, "lang": "EN", "Dim1": "T"}  # Dim1="T" = all periods
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(INE_URL, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.Timeout, requests.ConnectionError):
            if attempt == retries:
                raise
            wait_seconds = 15 * attempt
            print(f"{indicator_code}: attempt {attempt} failed, retrying in {wait_seconds}s")
            time.sleep(wait_seconds)

    cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def ine_json_to_dataframe(payload):
    """Flatten INE's {'Dados': {period: [records]}} structure into one row per period and place."""
    rows = []
    for period, records in payload[0]["Dados"].items():
        for record in records:
            rows.append({**record, "period": period})
    return pd.DataFrame(rows)


def describe_indicator(payload):
    """Print the indicator's name, last update and the period range it covers."""
    meta = payload[0]
    periods = list(meta["Dados"].keys())
    print(f"{meta['IndicadorCod']} | {meta['IndicadorDsg'][:110]}...")
    print(f"   last update: {meta['DataUltimoAtualizacao']} | {len(periods)} periods: "
          f"{periods[0]} -> {periods[-1]}")
