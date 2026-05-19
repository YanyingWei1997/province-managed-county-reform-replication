clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which oneclick
if _rc != 0 ssc install oneclick, replace

cap which tuples
if _rc != 0 ssc install tuples, replace

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* oneclick with TWFE method
oneclick `yvar' `controls', method(twfe) treated(D2) unit(county_code) time(year) horizon(10) preperiod(5) postperiod(0) cluster(county_code)

display "oneclick TWFE done"