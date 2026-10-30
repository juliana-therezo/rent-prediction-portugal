"""Project-wide settings: folders, data source codes and modelling constants.

Keeping these in one place means a notebook never hard-codes a path or a magic number.
"""
from pathlib import Path

# ---------- Folders ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
FIGURES_DIR = PROJECT_ROOT / "figures"
TABLEAU_DIR = PROJECT_ROOT / "tableau"

# ---------- INE (Statistics Portugal) API ----------
INE_URL = "https://www.ine.pt/ine/json_indicador/pindica.jsp"

INE_INDICATORS = {
    # Median rent €/m² of new long-term lease agreements, last 12 months, 2026 methodology, quarterly
    "rent": "0014696",
    # Number of new long-term lease agreements, last 12 months, 2026 methodology, quarterly
    "leases": "0014707",
    # Resident population by sex and age group, annual
    "population": "0012917",
}

# ---------- Clean outputs ----------
PANEL_FILE = CLEAN_DIR / "municipality_quarter_panel.csv"
MODEL_DATASET_FILE = CLEAN_DIR / "model_dataset.csv"

# ---------- Modelling ----------
# I predict the rent 4 quarters (= 1 year) after the moment the prediction is made.
# Test period: predictions made 2024 Q3 - 2025 Q2, i.e. rents of 2025 Q3 - 2026 Q2.
FORECAST_HORIZON_QUARTERS = 4
TEST_START_QUARTER = "2024Q3"
