clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which csdid
if _rc != 0 ssc install csdid

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

preserve
keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)
sort county_code year

* SA method（Sant'Anna & Zhao 2020，另一版本）
display "=== CS-DID with SA method ==="
csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(sa) long2

csdid_estat event
matrix BB = r(table)
local nc = colsof(BB)
local cnames : colnames BB

file open fcsd2 using "data/processed/es_csdid_sa.csv", write replace
file write fcsd2 "idx,colname,coef,se,ci_lower,ci_upper" _n
forvalues j = 1/`nc' {
    local cnm : word `j' of `cnames'
    local cv  = BB[1,`j']
    local sv  = BB[2,`j']
    local lv  = BB[5,`j']
    local uv  = BB[6,`j']
    file write fcsd2 "`j',`cnm',`cv',`sv',`lv',`uv'" _n
}
file close fcsd2
display "Saved: es_csdid_sa.csv"

restore
display "done"