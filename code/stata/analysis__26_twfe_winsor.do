clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar     "gdp_growth"

* 1% winsorize gdp_growth
_pctile `yvar', p(1, 99)
replace `yvar' = r(r1) if `yvar' < r(r1)
replace `yvar' = r(r2) if `yvar' > r(r2)

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* TWFE event study，winzorized
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 ///
    event_p8 event_p9 event_p10plus ///
    `controls', absorb(county_code year) cluster(county_code)

test event_m5 event_m4 event_m3 event_m2
display "Pre-trend F test (excl m1) p = " r(p)

* 保存 CSV
local periods "m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums   "-5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"

file open fwin using "data/processed/es_twfe_winsor.csv", write replace
file write fwin "period,coef,ci_lower,ci_upper,se" _n
file write fwin "0,0,0,0,0" _n

local i = 1
foreach p of local periods {
    local pnum : word `i' of `pnums'
    local bval = _b[event_`p']
    local seval = _se[event_`p']
    local loval = `bval' - 1.96 * `seval'
    local hival = `bval' + 1.96 * `seval'
    file write fwin "`pnum',`bval',`loval',`hival',`seval'" _n
    local i = `i' + 1
}
file close fwin
display "Saved: es_twfe_winsor.csv"

display "winsor done"