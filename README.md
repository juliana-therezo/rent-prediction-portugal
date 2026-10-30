# Predicting long-term rents in Portugal one year ahead

**Author:** Juliana Therezo · Ironhack Data Analytics Bootcamp · Machine Learning project (individual)
**Builds on:** [Rental crisis in Portugal](https://github.com/juliana-therezo/data-wrangling-project) (data-wrangling project)
**Slides:** Google Slides link: TODO (copy in `slides/`) · **Tableau dashboard:** `tableau/` (Tableau Public link: TODO) · **Kanban board:** TODO

---

## Objective

> What will the median **long-term** rent (€/m²) of new lease contracts be in each municipality of Portugal **one year from now**?

This is a **supervised regression** problem: I predict a number (rent in €/m²) from what is known today.
The project covers **long-term rentals only**: contracts people sign to live in a home. Short-term and tourist rentals are out of scope.

My previous project showed *that* rents grew faster than wages and that the pressure is spreading out of Lisbon and Porto.
This project turns that description into a **forecast**. A real estate investor, a family planning a move or a city council
could use it to see **where long-term rents are likely to rise the most**.

## Data sources

All data comes from [INE – Statistics Portugal](https://www.ine.pt/xportal/xmain?xpid=INE&xpgid=ine_api&INST=322751522&xlang=en) through its API (JSON), cached in `data/raw/`.

| Indicator | Content | Period |
|---|---|---|
| `0014696` | Median rent €/m² of new long-term lease contracts, last 12 months, by municipality (2026 methodology) | quarterly, 2020 Q1 – 2026 Q2 |
| `0014707` | Number of new long-term lease contracts, last 12 months, by municipality | quarterly, 2020 Q1 – 2026 Q2 |
| `0012917` | Resident population by age group, by municipality | annual, 2021 – 2025 |

Scope: the 278 municipalities of Portugal, without the Azores and Madeira.

## Repository structure

```
rent-prediction-portugal/
├── data/
│   ├── raw/                 # cached INE API responses
│   └── clean/               # municipality_quarter_panel.csv, model_dataset.csv
├── notebooks/
│   ├── 01_data_acquisition.ipynb               # problem definition + INE API
│   └── 02_data_preparation_and_modelling.ipynb # cleaning, features, EDA, models, tuning, results, forecast
├── src/
│   ├── config.py               # paths, indicator codes, constants
│   ├── data_acquisition.py     # INE API with local cache
│   ├── data_cleaning.py        # filtering, type fixes, panel building
│   ├── feature_engineering.py  # features and target
│   ├── evaluation.py           # time-based split, MAE / RMSE / R², top-20% hit rate
│   ├── modelling.py            # feature preparation (imputer, MinMaxScaler, one-hot) and the models
│   └── plots.py                # shared chart style and colours
├── figures/                 # charts used in the notebook
├── tableau/                 # CSV exports, workbook and dashboard guide
├── slides/                  # presentation
├── requirements.txt
└── README.md
```

**How to run:** `pip install -r requirements.txt`, then run the two notebooks in order from the `notebooks/` folder
(notebook 2 takes about two minutes because of the hyperparameter search).

## Methodology

### 1. Problem framing
- One row = one municipality in one quarter. Target = median long-term rent €/m² **4 quarters later**.
- Horizon of 4 quarters because INE's rent is a *last-12-months* median: a shorter horizon would overlap with data already known.

### 2. Data cleaning
- Kept the 278 municipalities in scope (7-character `geocod` starting with `1`).
- Converted text to numbers; INE's suppressed values (`'-'`, too few contracts) become NaN. The rent is **not** imputed.
- Parsed `"3rd Quarter 2024"` labels into pandas `Period` objects; pivoted population from long to wide.
- Joined everything on the 4-digit municipality code; built a **complete municipality × quarter grid** so that `shift(4)` always means one year.
- Result: **3,788 rows**, 230 municipalities, predictions made 2021 Q1 – 2025 Q2.

### 3. Features (7 numbers + 1 category)

| Feature | Meaning |
|---|---|
| `rent_m2` | rent today, €/m² |
| `rent_growth_1y` | rent growth over the last 12 months |
| `rent_vs_region` | rent today / median rent of the NUTS III region |
| `growth_vs_region` | last year's growth minus the region's growth |
| `log_new_leases` | size of the rental market (log of new contracts) |
| `leases_per_1000` | new contracts per 1,000 residents |
| `share_age_65_plus` | share of residents aged 65+ (previous year) |
| `area` | Lisbon metro / Porto metro / Rest of Portugal (one-hot encoded) |

**Feature selection:** correlation matrix. `log_population` was dropped because it is 0.96 correlated with `log_new_leases`.

### 4. Target in two simple steps

```
predicted rent = rent today x (1 + average growth of the training years + model prediction)
```

1. **Baseline:** every rent grows by the average growth of the training years (+10.8%).
2. **Machine learning:** the model predicts how much **faster or slower** than that average each municipality grows.

### 5. Train/test split and preparation
- **Split by time** (not at random). Train: predictions made 2021 Q1 – 2023 Q2 (2,055 rows). Test: predictions made 2024 Q3 – 2025 Q2,
  i.e. **rents of July 2025 – June 2026** (879 rows), the latest year INE has published.
- `SimpleImputer(mean)`, `MinMaxScaler` and `OneHotEncoder`, fitted on the training data only.

### 6. Models, cross-validation and tuning
- 7 regression models: Linear regression, KNN, Decision tree, Bagging, Random forest, AdaBoost, Gradient boosting.
- Compared with **5-fold cross-validation** (`cross_val_score`, `cv=5`) on the training data. Rows are sorted by municipality,
  so each fold holds different municipalities.
- **Hyperparameter tuning:**

| Model | Method | Best parameters | CV error before → after (pp) |
|---|---|---|---|
| Random forest | `GridSearchCV` | `max_depth=5`, `min_samples_leaf=20`, `n_estimators=300` | 4.65 → 4.64 |
| Gradient boosting | `RandomizedSearchCV` | `n_estimators=200`, `max_depth=4`, `learning_rate=0.01` | 4.79 → 4.62 |
| KNN | `GridSearchCV` | `n_neighbors=30` | 4.88 → 4.70 |

- **Final model:** the best cross-validation score, **tuned gradient boosting**.

## Key findings

### Historical evaluation – the evidence of performance (test year: rents of July 2025 – June 2026)

All accuracy figures compare predictions with real rents that INE has already published. The model never saw these rents while it
was trained or tuned.

| Model | MAE €/m² | RMSE €/m² | R² | Top-20% hit rate |
|---|---|---|---|---|
| Baseline: rent stays the same | 0.567 | 0.672 | 0.94 | – |
| Baseline: average growth (+10.8%) | **0.305** | 0.416 | 0.98 | – |
| Linear regression | 0.372 | 0.527 | 0.96 | 25% |
| Decision tree | 0.365 | 0.508 | 0.97 | 34% |
| AdaBoost | 0.352 | 0.475 | 0.97 | 37% |
| Bagging | 0.327 | 0.442 | 0.97 | 40% |
| Random forest (tuned) | 0.321 | 0.435 | 0.97 | 42% |
| KNN (tuned) | 0.311 | 0.435 | 0.97 | 35% |
| **Gradient boosting (tuned) – final** | **0.322** | **0.436** | **0.97** | **38%** |

1. **Accuracy:** the final model is wrong by **€0.32/m²** on average (about 6% of a typical rent of €5.84/m²). The simple
   "average growth" rule is about as accurate (€0.30/m²): machine learning does **not** reduce the € error.
2. **Ranking – where the model adds value:** a confusion matrix of "top 20% growth: yes / no" shows that when the model says a
   municipality will be in the top 20%, it is right **38%** of the time (precision), about **1.9× a random guess** (20%).
   Recall is 37%. Accuracy (75%) is not a useful number here because most municipalities are "not top 20%".
3. **Mean reversion:** the most important feature is growth compared with the region (`growth_vs_region`). Municipalities that grew
   faster than their neighbours tend to slow down, and cheaper ones tend to catch up.
4. **Errors by area:** Lisbon metro €0.44/m², Porto metro €0.30/m², Rest of Portugal €0.31/m². On average the model predicted slightly
   too high (€6.69 vs €6.53/m²), because rents grew less in the test year (+9.3%) than in the training years (+10.8%).

### 2027 outlook – application (Forecast — actual outcomes not yet available)

The same model, retrained on all data and applied to the latest quarter (2026 Q2), gives **estimates** for 2027 Q2. They show how
the model could be used in practice; they are not results and are not used for any accuracy claim.

- Among municipalities with 20,000+ residents, the highest estimated growth is in Santo Tirso (+17.8%), Arouca (+17.2%) and
  Oliveira de Azeméis (+16.6%), all in the Porto metro area, followed by Odemira (+14.9%); a typical municipality is about +10.7%.
- The estimates assume the market keeps its 2021–2025 average pace; if it keeps slowing, every estimate moves down.
- Coverage: 228 municipalities have a published rent in 2026 Q2 and therefore a forecast (117 with 20,000+ residents),
  out of 278 in scope.

## Limitations
- Only ~5 years of data, during an unusual boom; the average growth may not hold in a slowdown.
- Only municipalities with an active long-term rental market (≥ ~33 new contracts a year) have a published rent.
- Population for 2020–2021 quarters uses 2021 estimates (first year available).
- Nominal prices (not inflation-adjusted); INE covers declared leases only; no income, interest-rate or housing-supply data.

## Next steps
- Add macro data (interest rates, wages, inflation, housing completions) to predict the average growth itself.
- Add parish-level data (INE publishes it) to predict within Lisbon and Porto.
- Re-run every quarter with new INE data and track the 2027 forecast.
