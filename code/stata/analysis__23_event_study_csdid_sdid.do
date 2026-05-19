clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools
cap which csdid
if _rc != 0 {
    ssc install csdid
    ssc install drdid
}

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* ============================================================
* 1. TWFE event study
* ============================================================
local periods "m6plus m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums   "-6 -5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"

reghdfe `yvar' event_m6plus event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 ///
    event_p8 event_p9 event_p10plus ///
    `controls', absorb(county_code year) cluster(county_code)

file open ftwfe using "data/processed/es_twfe.csv", write replace
file write ftwfe "period,coef,ci_lower,ci_upper,se" _n
file write ftwfe "0,0,0,0,0" _n

local i = 1
foreach p of local periods {
    local pnum : word `i' of `pnums'
    local bval = _b[event_`p']
    local seval = _se[event_`p']
    local loval = `bval' - 1.96 * `seval'
    local hival = `bval' + 1.96 * `seval'
    file write ftwfe "`pnum',`bval',`loval',`hival',`seval'" _n
    local i = `i' + 1
}
file close ftwfe
display "Saved: es_twfe.csv"

* ============================================================
* 2. CS-DID event study
* ============================================================
preserve
keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)
sort county_code year

cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(drimp) long2
if _rc != 0 {
    display "drimp failed, try reg"
    csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(reg) long2
}

csdid_estat event
matrix BB = r(table)
local nc = colsof(BB)
local cnames : colnames BB
display "CS-DID cols: `nc'"
display "Names: `cnames'"

file open fcsd using "data/processed/es_csdid_raw.csv", write replace
file write fcsd "idx,colname,coef,se,ci_lower,ci_upper" _n

forvalues jj = 1/`nc' {
    local cnm : word `jj' of `cnames'
    local cv = BB[1,`jj']
    local sv = BB[2,`jj']
    local lv = BB[5,`jj']
    local uv = BB[6,`jj']
    file write fcsd "`jj',`cnm',`cv',`sv',`lv',`uv'" _n
}
file close fcsd
display "Saved: es_csdid_raw.csv"
restore

display "23 done"
