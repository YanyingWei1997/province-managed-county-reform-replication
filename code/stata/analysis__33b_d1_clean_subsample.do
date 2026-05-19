clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T33B: D1 panel ATT on never-D2 subsample (clean comparison)
* 排除 218 个 D1+D2 双采纳县，避免 CS-DID D1 估计被 D2 效应污染
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* ============================================================
* 0. 构造 never-D2 子样本
* ============================================================
bysort county_code: egen d2_ever = max(D2)

* 保留 never-D2 县
keep if d2_ever == 0
drop d2_ever

* 子样本统计
quietly count
display "Never-D2 sub-sample observations: " r(N)

bysort county_code: egen d1_ever = max(D1)
quietly count if d1_ever == 1 & year == 2000
local n_d1_only = r(N)
quietly count if d1_ever == 0 & year == 2000
local n_neither = r(N)
display "Never-D2 sub-sample: D1-only counties = `n_d1_only', neither D1 nor D2 = `n_neither'"
drop d1_ever

* ============================================================
* 1. TWFE D1 (clean sub-sample)
* ============================================================
display "========== TWFE D1 (never-D2 sub-sample) =========="

reghdfe `yvar' D1 `controls', absorb(county_code year) cluster(county_code)

local d1_clean_coef = _b[D1]
local d1_clean_se   = _se[D1]
local d1_clean_t    = `d1_clean_coef' / `d1_clean_se'
local d1_clean_p    = 2 * (1 - normal(abs(`d1_clean_t')))
local d1_clean_ci_lo = `d1_clean_coef' - 1.96 * `d1_clean_se'
local d1_clean_ci_hi = `d1_clean_coef' + 1.96 * `d1_clean_se'
local d1_clean_n    = e(N)

display "TWFE D1 (clean) coef = " `d1_clean_coef'
display "TWFE D1 (clean) SE   = " `d1_clean_se'
display "TWFE D1 (clean) p    = " `d1_clean_p'

* ============================================================
* 2. CS-DID D1 (clean sub-sample)
* ============================================================
display "========== CS-DID D1 (never-D2 sub-sample) =========="

bysort county_code: egen gvar_d1_max = max(D1_year)
gen int gvar_d1 = int(gvar_d1_max)
drop gvar_d1_max
replace gvar_d1 = 0 if missing(gvar_d1)
replace gvar_d1 = 0 if gvar_d1 < 2000

tab gvar_d1, missing

preserve
keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)

sort county_code year

quietly count
local csdid_clean_n = r(N)
display "CS-DID D1 clean sample size: " `csdid_clean_n'

cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar_d1) method(drimp)
if _rc != 0 | e(N)==0 {
    display "drimp failed, fallback to method(reg)"
    csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar_d1) method(reg)
}

csdid_estat simple

matrix res = r(table)
local d1_csdid_clean_coef = res[1,1]
local d1_csdid_clean_se   = res[2,1]
local d1_csdid_clean_ci_lo = res[5,1]
local d1_csdid_clean_ci_hi = res[6,1]

display "CS-DID D1 (clean) ATT(simple) = " `d1_csdid_clean_coef'
display "CS-DID D1 (clean) SE          = " `d1_csdid_clean_se'
display "CS-DID D1 (clean) CI: [" `d1_csdid_clean_ci_lo' ", " `d1_csdid_clean_ci_hi' "]"
restore

* ============================================================
* 3. 写入到 table_d1_d2_panel.csv (追加)
* ============================================================
file open fout using "outputs/tables/table_d1_d2_panel.csv", write append
file write fout "TWFE_D1_clean,D1,`d1_clean_coef',`d1_clean_se',`d1_clean_ci_lo',`d1_clean_ci_hi',`d1_clean_p',`d1_clean_n'" _n
file write fout "CSDID_D1_clean,D1,`d1_csdid_clean_coef',`d1_csdid_clean_se',`d1_csdid_clean_ci_lo',`d1_csdid_clean_ci_hi',,`csdid_clean_n'" _n
file close fout

display "=========================================="
display "T33B SUMMARY (never-D2 sub-sample)"
display "TWFE D1 clean:  coef=`d1_clean_coef', SE=`d1_clean_se', p=`d1_clean_p'"
display "CSDID D1 clean: coef=`d1_csdid_clean_coef', SE=`d1_csdid_clean_se'"
display "=========================================="
