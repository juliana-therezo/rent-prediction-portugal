# Tableau workbook: Long-term rent outlook 2027 – Portugal

Two dashboards:

- **Historical test 2025–2026** – the evidence: predicted vs real rents of July 2025 – June 2026, errors and comparison with simple rules.
- **2027 outlook (forecast)** – the application, labelled *Forecast — actual outcomes not yet available*: estimated rents for 2027 Q2 by municipality.

<!-- original build guide below -->

## Build guide (first version)

The prediction notebook answers "how good is the model?". This dashboard answers what a user of the model wants to know:
**which municipalities are expected to see the highest long-term rent growth, and how have their rents evolved?**

The three CSV files in this folder are created by `notebooks/02_data_preparation_and_modelling.ipynb` (section 11).

| File | One row = | Main columns |
|---|---|---|
| `forecast_2027.csv` | municipality | `municipality`, `region_name`, `area`, `population`, `rent_2026q2`, `forecast_rent_2027q2`, `forecast_growth_pct`, `vs_portugal_pp`, `rank` |
| `rent_history.csv` | municipality × quarter, 2020 Q1 – 2026 Q2 | `municipality`, `region_name`, `area`, `quarter`, `quarter_start_date`, `rent_m2`, `new_leases` |
| `test_predictions.csv` | municipality × quarter of the test year | `municipality`, `area`, `quarter_predicted`, `target_rent_next_year` (real), `predicted_rent_next_year`, `error_eur_m2` |

## Colours (same rule as the slides and the notebook)

Orange and navy are **only** used for the Lisbon and Porto metro areas. Every other chart uses the "Rest of Portugal" blue or greys.

| Role | Hex | Use it for |
|---|---|---|
| Lisbon metro | `#C87B29` | marks of Lisbon metro municipalities only |
| Porto metro | `#404F7A` | marks of Porto metro municipalities only |
| Rest of Portugal | `#8D9DBE` | marks of the rest of Portugal; highlight colour of charts that are not about areas |
| Greys | `#D7D6DB` / `#B3B3BA` / `#4A4D57` | other bars, reference lines, borders; "today vs 2027" uses light grey (today) and dark grey (2027 estimate) |
| Background | `#FAFAFA` / `#EFEFF2` | dashboard background / note boxes |
| Text | `#1A1A1A` / `#5A5F6E` | titles and KPI numbers / labels and captions |

## Build steps (Tableau Public / Desktop)

1. **Connect** to `forecast_2027.csv`, then add `rent_history.csv` and `test_predictions.csv` as separate data sources.
   In each source, set `municipality_code` to *String* and `quarter_start_date` to *Date*.
2. **Relationship** (forecast ↔ history): relate the two sources on `municipality_code`, so one filter works on both.

### Sheet 1 – "Top municipalities" (bar chart)
- Rows: `municipality`; Columns: `forecast_growth_pct` (AVG). Sort descending, show the top 15 (Filter → Top → 15 by `forecast_growth_pct`).
- Colour: `area` (Lisbon / Porto / Rest of Portugal palette); Label: `forecast_growth_pct` formatted `+0.0"%"`.
- Filters (show as controls): `area`, `region_name`, `population` (range slider, default ≥ 20,000).

### Sheet 2 – "Rent history" (line chart)
- Columns: `quarter_start_date` (continuous quarter); Rows: `rent_m2` (AVG).
- Colour: `area` (Lisbon metro `#C87B29`, Porto metro `#404F7A`, Rest of Portugal `#8D9DBE`).
- This sheet is filtered by clicking a bar in Sheet 1 (dashboard action, step 6).

### Sheet 3 – "Today vs 2027" (dumbbell or table)
- Rows: `municipality`; Columns: `rent_2026q2` and `forecast_rent_2027q2` (Measure Values, circle marks), to show today's rent and the forecast side by side.

### Sheet 4 – "Can I trust it?" (scatter)
- Source `test_predictions.csv`. Columns: `target_rent_next_year`; Rows: `predicted_rent_next_year`; Colour: `area`.
- Add a reference line y = x (calculated field `[target_rent_next_year]` on a dual axis, synchronised) and a caption:
  *"Test year (rents of 2025 Q3 – 2026 Q2): average error €0.32/m²."*

### KPI tiles (text sheets)
- Median `rent_2026q2`, median `forecast_rent_2027q2`, median `forecast_growth_pct`, count of municipalities.

### Optional – map
- Give `municipality` the geographic role *County* and Country = Portugal. If Tableau does not recognise all
  names, skip the map rather than plotting a partial one.

## Dashboard
5. **Layout (1200 × 800):** title "Long-term rent outlook 2027 – Portugal" at the top, KPI tiles in a row below it,
   Sheet 1 on the left (≈ 55 % width), Sheet 2 above Sheet 3 on the right, Sheet 4 at the bottom or on a second tab.
6. **Actions:** Dashboard → Actions → Filter: source Sheet 1, target Sheets 2 and 3, run on *Select*.
7. **Note on the dashboard (text box):** "Forecast assumes the market keeps growing at its 2021–2025 average (+10.7 % a year).
   The ranking is more reliable than the exact %."
8. Publish to Tableau Public and paste the link in the main README.
