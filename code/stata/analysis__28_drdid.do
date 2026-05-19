clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which drdid
if _rc != 0 ssc install drdid

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

* DR-DID 事件研究
drdid `yvar' `controls', ivar(county_code) time(year) treatment(D2) gvar(gvar) long2

* 事件研究
drdid_estat event
matrix BB = r(table)
local nc = colsof(BB)
local cnames : colnames BB
display "DR-DID cols (`nc'): `cnames'"

file open fdrd using "data/processed/es_drdid.csv", write replace
file write fdrd "idx,colname,coef,se,ci_lower,ci_upper" _n
forvalues j = 1/`nc' {
    local cnm : word `j' of `cnames'
    local cv  = BB[1,`j']
    local sv  = BB[2,`j']
    local lv  = BB[5,`j']
    local uv  = BB[6,`j']
    file write fdrd "`j',`cnm',`cv',`sv',`lv',`uv'" _n
}
file close fdrd
display "Saved: es_drdid.csv"

restore
display "28 done"