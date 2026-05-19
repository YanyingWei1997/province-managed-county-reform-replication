clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T33: D1 (扩权强县) 基准 TWFE / CS-DID 对照估计
* 与 D2 (T03B) 平行，用于 D1 vs D2 制度对比的实证支撑
* ============================================================

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which csdid
if _rc != 0 ssc install csdid
cap which drdid
if _rc != 0 ssc install drdid

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T33: D1 panel ATT estimation"
display "Outcome: `yvar'"
display "Controls: `controls'"
display "=========================================="

* ============================================================
* 0. 数据诊断: D1 / D1_year 变量是否存在
* ============================================================
cap confirm variable D1
if _rc != 0 {
    display "ERROR: variable D1 not found in dataset"
    exit 198
}

cap confirm variable D1_year
if _rc != 0 {
    display "ERROR: variable D1_year not found in dataset"
    exit 198
}

* D1 / D1_year 描述性统计
quietly count if D1 == 1
display "D1 == 1 county-year observations: " r(N)
quietly count
display "Total observations: " r(N)

quietly count if !missing(D1_year)
display "D1_year non-missing observations: " r(N)

bysort county_code: egen d1_max = max(D1)
quietly count if d1_max == 1 & year == 2000
display "Counties ever-treated by D1: " r(N)
drop d1_max

bysort county_code: egen d1y_max = max(D1_year)
quietly summarize d1y_max
display "D1_year stats: min=" r(min) ", max=" r(max)
drop d1y_max

* ============================================================
* 1. TWFE 基准回归 (D1)
* ============================================================
display "========== TWFE D1 回归 =========="

reghdfe `yvar' D1 `controls', absorb(county_code year) cluster(county_code)

local d1_twfe_coef = _b[D1]
local d1_twfe_se   = _se[D1]
local d1_twfe_t    = `d1_twfe_coef' / `d1_twfe_se'
local d1_twfe_p    = 2 * (1 - normal(abs(`d1_twfe_t')))
local d1_twfe_ci_lo = `d1_twfe_coef' - 1.96 * `d1_twfe_se'
local d1_twfe_ci_hi = `d1_twfe_coef' + 1.96 * `d1_twfe_se'
local d1_twfe_n    = e(N)

display "TWFE D1 coef = " `d1_twfe_coef'
display "TWFE D1 SE   = " `d1_twfe_se'
display "TWFE D1 p    = " `d1_twfe_p'
display "TWFE D1 CI: [" `d1_twfe_ci_lo' ", " `d1_twfe_ci_hi' "]"
display "TWFE D1 N    = " `d1_twfe_n'

* ============================================================
* 2. TWFE 同时含 D1 与 D2 (检查 D2 估计是否对 D1 控制稳健)
* ============================================================
display "========== TWFE 同时含 D1 与 D2 =========="

reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)

local d2_jw_coef = _b[D2]
local d2_jw_se   = _se[D2]
local d2_jw_p    = 2 * (1 - normal(abs(`d2_jw_coef'/`d2_jw_se')))
local d2_jw_ci_lo = `d2_jw_coef' - 1.96 * `d2_jw_se'
local d2_jw_ci_hi = `d2_jw_coef' + 1.96 * `d2_jw_se'

local d1_jw_coef = _b[D1]
local d1_jw_se   = _se[D1]
local d1_jw_p    = 2 * (1 - normal(abs(`d1_jw_coef'/`d1_jw_se')))
local d1_jw_ci_lo = `d1_jw_coef' - 1.96 * `d1_jw_se'
local d1_jw_ci_hi = `d1_jw_coef' + 1.96 * `d1_jw_se'

display "TWFE D2 (joint) coef = " `d2_jw_coef' ", SE = " `d2_jw_se' ", p = " `d2_jw_p'
display "TWFE D1 (joint) coef = " `d1_jw_coef' ", SE = " `d1_jw_se' ", p = " `d1_jw_p'

* ============================================================
* 3. CS-DID for D1
* ============================================================
display "========== CS-DID D1 回归 =========="

bysort county_code: egen gvar_d1_max = max(D1_year)
gen int gvar_d1 = int(gvar_d1_max)
drop gvar_d1_max
replace gvar_d1 = 0 if missing(gvar_d1)
replace gvar_d1 = 0 if gvar_d1 < 2000

label variable gvar_d1 "D1 改革年份 (0 = 从不处理或 2000 前)"

tab gvar_d1, missing

preserve
keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)

sort county_code year

quietly count
local csdid_d1_n = r(N)
display "CS-DID D1 sample size: " `csdid_d1_n'

cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar_d1) method(drimp)
if _rc != 0 | e(N)==0 {
    display "drimp failed, fallback to method(reg)"
    csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar_d1) method(reg)
}

csdid_estat simple

matrix res = r(table)
local d1_csdid_coef = res[1,1]
local d1_csdid_se   = res[2,1]
local d1_csdid_ci_lo = res[5,1]
local d1_csdid_ci_hi = res[6,1]

display "CS-DID D1 ATT(simple) = " `d1_csdid_coef'
display "CS-DID D1 SE          = " `d1_csdid_se'
display "CS-DID D1 CI: [" `d1_csdid_ci_lo' ", " `d1_csdid_ci_hi' "]"
restore

* ============================================================
* 4. 汇总输出 table_d1_d2_panel.csv
* ============================================================
file open fout using "outputs/tables/table_d1_d2_panel.csv", write replace
file write fout "spec,treatment,coef,se,ci_lower,ci_upper,p,N" _n
file write fout "TWFE_D1_only,D1,`d1_twfe_coef',`d1_twfe_se',`d1_twfe_ci_lo',`d1_twfe_ci_hi',`d1_twfe_p',`d1_twfe_n'" _n
file write fout "TWFE_joint,D1,`d1_jw_coef',`d1_jw_se',`d1_jw_ci_lo',`d1_jw_ci_hi',`d1_jw_p',`d1_twfe_n'" _n
file write fout "TWFE_joint,D2,`d2_jw_coef',`d2_jw_se',`d2_jw_ci_lo',`d2_jw_ci_hi',`d2_jw_p',`d1_twfe_n'" _n
file write fout "CSDID_D1,D1,`d1_csdid_coef',`d1_csdid_se',`d1_csdid_ci_lo',`d1_csdid_ci_hi',,`csdid_d1_n'" _n
file close fout

display "Results written to outputs/tables/table_d1_d2_panel.csv"

display "=========================================="
display "T33 SUMMARY"
display "TWFE D1 alone:        coef=`d1_twfe_coef', SE=`d1_twfe_se', p=`d1_twfe_p'"
display "TWFE D2 (joint w/D1): coef=`d2_jw_coef', SE=`d2_jw_se', p=`d2_jw_p'"
display "TWFE D1 (joint w/D2): coef=`d1_jw_coef', SE=`d1_jw_se', p=`d1_jw_p'"
display "CSDID D1:             coef=`d1_csdid_coef', SE=`d1_csdid_se'"
display "=========================================="
