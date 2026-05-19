clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T37: Hainan 剔除稳健性 + D1 cohort 分布报告
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T37: Pre-2000 treated exclusion + D1 cohorts"
display "=========================================="

* ============================================================
* 1. 识别 pre-2000 已处理县（Hainan 等）
* ============================================================
bysort county_code: egen min_d2_year = min(D2_year)

* 检查 pre-2000 处理县
quietly count if min_d2_year < 2000 & min_d2_year != . & year == 2000
display "Pre-2000 D2-treated counties: " r(N)

* 也按省份显示
preserve
keep if year == 2000 & min_d2_year < 2000 & min_d2_year != .
tab province min_d2_year, missing
restore

* ============================================================
* 2. 剔除 pre-2000 处理县后的基准 TWFE D2
* ============================================================
display "========== TWFE D2 (excluding pre-2000 treated) =========="
preserve
drop if min_d2_year < 2000 & min_d2_year != .
quietly count
display "Sample after excluding pre-2000: " r(N)

reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local b_excl_coef = _b[D2]
local b_excl_se = _se[D2]
local b_excl_p = 2*(1 - normal(abs(`b_excl_coef'/`b_excl_se')))
local b_excl_lo = `b_excl_coef' - 1.96*`b_excl_se'
local b_excl_hi = `b_excl_coef' + 1.96*`b_excl_se'
local b_excl_n = e(N)
display "TWFE D2 (excl pre-2000): coef=" `b_excl_coef' " SE=" `b_excl_se' " p=" `b_excl_p'
restore

* ============================================================
* 3. D1 cohort 分布报告
* ============================================================
display "========== D1 cohort distribution =========="
bysort county_code: egen min_d1_year = min(D1_year)

* D1 处理县总数
quietly count if min_d1_year != . & min_d1_year >= 2000 & year == 2000
local d1_n_treated = r(N)
display "Counties ever-treated by D1 (with D1_year >= 2000): " `d1_n_treated'

* D1 cohort 数（不同 D1_year 数）
preserve
keep if year == 2000 & min_d1_year != . & min_d1_year >= 2000
quietly levelsof min_d1_year, local(d1_cohorts)
local d1_n_cohorts : word count `d1_cohorts'
display "D1 unique cohort years (>=2000): " `d1_n_cohorts'
display "D1 cohort years: `d1_cohorts'"

* 每个 cohort 的县数
display "Cohort distribution:"
tab min_d1_year
restore

* D2 cohort 数（对比）
preserve
keep if year == 2000 & min_d2_year != . & min_d2_year >= 2000
quietly levelsof min_d2_year, local(d2_cohorts)
local d2_n_cohorts : word count `d2_cohorts'
display "D2 unique cohort years (>=2000): " `d2_n_cohorts'
display "D2 cohort years: `d2_cohorts'"
restore

* ============================================================
* 4. 输出结果
* ============================================================
file open fout using "outputs/tables/table_hainan_d1cohort.csv", write replace
file write fout "spec,coef,se,ci_lower,ci_upper,p,N,note" _n
file write fout "TWFE_D2_excl_pre2000,`b_excl_coef',`b_excl_se',`b_excl_lo',`b_excl_hi',`b_excl_p',`b_excl_n',pre-2000 treated counties dropped" _n
file write fout "D1_n_cohorts,,,,,,,Total D1 cohort years (>=2000): `d1_n_cohorts'" _n
file write fout "D2_n_cohorts,,,,,,,Total D2 cohort years (>=2000): `d2_n_cohorts'" _n
file close fout

display "=========================================="
display "T37 SUMMARY"
display "Baseline TWFE D2 (full sample): 1.023 pp"
display "TWFE D2 (excl pre-2000):        `b_excl_coef' (SE `b_excl_se', p `b_excl_p')"
display "D1 cohort years count:          `d1_n_cohorts'"
display "D2 cohort years count:          `d2_n_cohorts'"
display "=========================================="
