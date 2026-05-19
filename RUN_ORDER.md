# Recommended Run Order

Run commands from the replication package root. The order below follows the analysis pipeline used in the revised manuscript.

## 1. Data checks and derived datasets

```stata
do code/stata/data_cleaning__03_data_structure_check.do
do code/stata/data_cleaning__04_grf_covariates.do
do code/stata/data_cleaning__05_grf_merge.do
do code/stata/data_cleaning__06_dml_panel.do
```

## 2. Main average effects and event-study evidence

```stata
do code/stata/analysis__03b_baseline_did.do
do code/stata/analysis__20_synthetic_did.do
do code/stata/analysis__22_event_study_multi.do
do code/stata/analysis__23_event_study_csdid_sdid.do
do code/stata/analysis__24_sunab_event_study.do
do code/stata/analysis__25_did2s_event_study.do
```

## 3. GRF, heterogeneity, and PolicyTree diagnostics

```bash
python code/python/analysis/09_causal_forest_d2.py
python code/python/analysis/10_grf_d2_validate.py
python code/python/analysis/11_causal_forest_d1.py
python code/python/analysis/12_policy_tree.py
python code/python/analysis/13_cate_heterogeneity.py
```

## 4. DML channel analysis

```bash
python code/python/analysis/14_double_ml_baseline.py
python code/python/analysis/15_dml_step1_fiscal.py
python code/python/analysis/16_dml_step2_fiscal.py
python code/python/analysis/17_dml_mediation_exp.py
```

## 5. Reviewer-requested robustness and sensitivity checks

```stata
do code/stata/analysis__35_province_year_fe.do
do code/stata/analysis__42_missing_analysis.do
do code/stata/analysis__43b_placebo_year_permutation.do
do code/stata/analysis__51_provclust.do
do code/stata/analysis__51b_provclust_boottest.do
do code/stata/analysis__52_dualadopter.do
do code/stata/analysis__53_anticipation.do
do code/stata/analysis__55_taxrev_robust.do
do code/stata/analysis__56_pre_covid.do
do code/stata/analysis__59_missingness_sensitivity.do
```

```bash
python code/python/analysis/50_honest_did.py
python code/python/analysis/60_multiple_imputation_missingness.py
```

## 6. Final tables and figures

```bash
python code/python/visualization/22_final_figures.py
python code/python/visualization/23_result_tables.py
python code/python/visualization/40_spatial_cate_map.py
python code/python/visualization/41_regional_drivers_table.py
```

The package also includes generated outputs in `outputs/tables/` and `outputs/figures/` so readers can inspect reported values without re-running every estimator.
