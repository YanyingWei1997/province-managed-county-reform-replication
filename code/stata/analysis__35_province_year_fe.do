clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T35: Province x Year FE 稳健性检验
* 检验 D2 估计在控制省级时变冲击后是否稳健
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T35: Province x Year FE robustness"
display "=========================================="

* 省份代码
encode province, gen(prov_code)
gen prov_year = prov_code * 10000 + year

display "Total observations: " _N

quietly count if !missing(prov_code)
display "Non-missing province: " r(N)

* ============================================================
* 1. 基准 TWFE (county + year FE) -- 复现表 1
* ============================================================
display "========== 基准 TWFE =========="
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)

local b1_coef = _b[D2]
local b1_se = _se[D2]
local b1_p = 2*(1 - normal(abs(`b1_coef'/`b1_se')))
local b1_lo = `b1_coef' - 1.96*`b1_se'
local b1_hi = `b1_coef' + 1.96*`b1_se'
local b1_n = e(N)
display "Baseline TWFE D2: coef=" `b1_coef' " SE=" `b1_se' " p=" `b1_p'

* ============================================================
* 2. TWFE 增加 Province x Year FE
* ============================================================
display "========== TWFE + Province x Year FE =========="
reghdfe `yvar' D2 `controls', absorb(county_code year prov_year) cluster(county_code)

local b2_coef = _b[D2]
local b2_se = _se[D2]
local b2_p = 2*(1 - normal(abs(`b2_coef'/`b2_se')))
local b2_lo = `b2_coef' - 1.96*`b2_se'
local b2_hi = `b2_coef' + 1.96*`b2_se'
local b2_n = e(N)
display "TWFE + ProvxYear FE D2: coef=" `b2_coef' " SE=" `b2_se' " p=" `b2_p'

* ============================================================
* 3. TWFE 仅 Province x Year FE (drop year FE 因为被吸收)
* ============================================================
display "========== TWFE + ProvxYear (no separate year FE) =========="
reghdfe `yvar' D2 `controls', absorb(county_code prov_year) cluster(county_code)

local b3_coef = _b[D2]
local b3_se = _se[D2]
local b3_p = 2*(1 - normal(abs(`b3_coef'/`b3_se')))
local b3_lo = `b3_coef' - 1.96*`b3_se'
local b3_hi = `b3_coef' + 1.96*`b3_se'
local b3_n = e(N)
display "TWFE w/ ProvxYear only D2: coef=" `b3_coef' " SE=" `b3_se' " p=" `b3_p'

* ============================================================
* 4. 输出汇总
* ============================================================
file open fout using "outputs/tables/table_provyear_robust.csv", write replace
file write fout "spec,coef,se,ci_lower,ci_upper,p,N" _n
file write fout "TWFE_baseline,`b1_coef',`b1_se',`b1_lo',`b1_hi',`b1_p',`b1_n'" _n
file write fout "TWFE_plus_provyear,`b2_coef',`b2_se',`b2_lo',`b2_hi',`b2_p',`b2_n'" _n
file write fout "TWFE_provyear_only,`b3_coef',`b3_se',`b3_lo',`b3_hi',`b3_p',`b3_n'" _n
file close fout

display "=========================================="
display "T35 SUMMARY"
display "Baseline TWFE D2:           coef=`b1_coef', SE=`b1_se', p=`b1_p'"
display "TWFE + Prov x Year FE D2:   coef=`b2_coef', SE=`b2_se', p=`b2_p'"
display "TWFE w/ Prov x Year only:   coef=`b3_coef', SE=`b3_se', p=`b3_p'"
display "=========================================="
