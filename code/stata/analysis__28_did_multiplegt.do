clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which did_multiplegt
if _rc != 0 ssc install did_multiplegt

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar "gdp_growth"

* gvar: first treatment year
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* did_multiplegt 事件研究（自动逐期）
did_multiplegt `yvar' county_code year D2, ///
    covariates(`controls') ///
    cluster(county_code) ///
    long2 ///
    placebo(5) ///
    breps(200) ///
    dynamic(10) ///
    save("data/processed/did_mg_results.csv") ///
    replace

display "done"