clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which did_imputation
if _rc != 0 ssc install did_imputation

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar     "gdp_growth"

* treatment timing variable: year of first D2 treatment, missing = never treated
bysort county_code: egen gvar_max = max(D2_year)
gen Ei = int(gvar_max)
drop gvar_max
replace Ei = . if missing(Ei)
replace Ei = . if Ei < 2000

* ============================================================
* Borusyak, Jaravel & Spiess (2021) imputation estimator
* ============================================================
did_imputation `yvar' county_code year Ei, ///
    horizons(0/10) pretrends(5) ///
    controls(`controls') ///
    cluster(county_code) ///
    autosample

* 保存逐期系数
matrix B  = e(b)
matrix V  = e(V)
local cnames : colnames B
local nc = colsof(B)
display "BJS cols (`nc'): `cnames'"

file open fbjs using "data/processed/es_bjs_raw.csv", write replace
file write fbjs "idx,colname,coef,se,ci_lower,ci_upper" _n
forvalues j = 1/`nc' {
    local cn : word `j' of `cnames'
    local cv = B[1, `j']
    local sv = sqrt(V[`j',`j'])
    local lv = `cv' - 1.96*`sv'
    local uv = `cv' + 1.96*`sv'
    file write fbjs "`j',`cn',`cv',`sv',`lv',`uv'" _n
}
file close fbjs
display "Saved: es_bjs_raw.csv"

* 预趋势联合检验
display _n "=== BJS Pre-trend test ==="
bhtest

display "25 done"
