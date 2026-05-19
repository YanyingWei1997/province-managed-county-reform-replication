# Data Dictionary

## `data/analysis/panel_analysis_public.csv` / `.dta`

This is a partial analysis-ready panel derived from the compiled county-year dataset. It excludes raw source sheets and Chinese name fields.

| Variable | Description |
|---|---|
| `year` | Calendar year, 2000-2023. |
| `county_code` | Numeric county administrative identifier. |
| `D` | Indicator for any reform exposure. |
| `D1` | Strengthening county authority reform indicator. |
| `D2` | Province-managed-county fiscal reform indicator. |
| `reform_year` | First year of any reform exposure. |
| `D1_year` | First D1 reform year. |
| `D2_year` | First D2 reform year. |
| `gdp_growth_pc` | Per-capita GDP growth rate, percentage points; main outcome. |
| `ln_gdppc` | Log GDP per capita; robustness outcome. |
| `gdppc` | GDP per capita level, retained for selected auxiliary scripts. |
| `ln_fiscal_exp_pc` | Log fiscal expenditure per capita. |
| `ln_fiscal_rev_pc` | Log fiscal revenue per capita. |
| `fiscal_autonomy` | Fiscal revenue divided by fiscal expenditure. |
| `transfer_dependence` | Transfer-dependence proxy. |
| `fiscal_exp_pc` | Fiscal expenditure per capita. |
| `fiscal_rev_pc` | Fiscal revenue per capita. |
| `primary_ratio` | Primary-sector share. |
| `secondary_ratio` | Secondary-sector share. |
| `tertiary_ratio` | Tertiary-sector share. |
| `ln_pop` | Log population. |
| `gov_scale` | Government scale control. |
| `high_development` | High-development county indicator. |
| `high_agriculture` | High-agriculture county indicator. |
| `is_county_city` | County-level city indicator. |
| `region` | Region label. |
| `region_east` | Eastern region dummy. |
| `region_central` | Central region dummy. |
| `region_west` | Western region dummy. |
| `relative_time` | Relative time to reform. |
| `event_m6plus` | Event-study relative-time indicator. |
| `event_m5` | Event-study relative-time indicator. |
| `event_m4` | Event-study relative-time indicator. |
| `event_m3` | Event-study relative-time indicator. |
| `event_m2` | Event-study relative-time indicator. |
| `event_m1` | Event-study relative-time indicator. |
| `event_0` | Event-study relative-time indicator. |
| `event_p1` | Event-study relative-time indicator. |
| `event_p2` | Event-study relative-time indicator. |
| `event_p3` | Event-study relative-time indicator. |
| `event_p4` | Event-study relative-time indicator. |
| `event_p5` | Event-study relative-time indicator. |
| `event_p6` | Event-study relative-time indicator. |
| `event_p7` | Event-study relative-time indicator. |
| `event_p8` | Event-study relative-time indicator. |
| `event_p9` | Event-study relative-time indicator. |
| `event_p10plus` | Event-study relative-time indicator. |

## Derived datasets

- `data/processed/grf_input.csv`: county-level GRF input with pre-reform covariates and post-reform outcomes.
- `data/processed/d2_cate_results.csv`: D2 CATE output from GRF.
- `data/processed/d1_cate_results.csv`: D1 CATE output from GRF.
- `data/processed/dml_panel.csv`: DML panel input before within transformation.
- `data/processed/dml_panel_within.csv`: DML panel after two-way within transformation.
- `data/processed/es_*.csv`: event-study coefficient series used for dynamic-effect figures.
