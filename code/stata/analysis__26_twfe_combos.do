clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools

local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* 控制变量组合测试
cap file close fcombo
file open fcombo using "data/processed/combo_results.csv", write replace
file write fcombo "combo,controls,pre_p,coef_m1,ci_lo,ci_hi" _n

* combo 1: full
display "=== Combo 1: full ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus primary_ratio secondary_ratio ln_pop gov_scale, absorb(county_code year) cluster(county_code)
test event_m5 event_m4 event_m3 event_m2
local pp = r(p)
local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
file write fcombo "1,full,`pp',`bm1',`bm1'-1.96*`sm1',`bm1'+1.96*`sm1'" _n
display "Pre-trend p=" `pp' "  t=-1: coef=" `bm1' " CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

* combo 2: no gov_scale
display "=== Combo 2: no_govs ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus primary_ratio secondary_ratio ln_pop, absorb(county_code year) cluster(county_code)
test event_m5 event_m4 event_m3 event_m2
local pp = r(p)
local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
file write fcombo "2,no_govs,`pp',`bm1',`bm1'-1.96*`sm1',`bm1'+1.96*`sm1'" _n
display "Pre-trend p=" `pp' "  t=-1: coef=" `bm1' " CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

* combo 3: no ln_pop
display "=== Combo 3: no_lnpop ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus primary_ratio secondary_ratio gov_scale, absorb(county_code year) cluster(county_code)
test event_m5 event_m4 event_m3 event_m2
local pp = r(p)
local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
file write fcombo "3,no_lnpop,`pp',`bm1',`bm1'-1.96*`sm1',`bm1'+1.96*`sm1'" _n
display "Pre-trend p=" `pp' "  t=-1: coef=" `bm1' " CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

* combo 4: rr only
display "=== Combo 4: rr_only ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus primary_ratio secondary_ratio, absorb(county_code year) cluster(county_code)
test event_m5 event_m4 event_m3 event_m2
local pp = r(p)
local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
file write fcombo "4,rr_only,`pp',`bm1',`bm1'-1.96*`sm1',`bm1'+1.96*`sm1'" _n
display "Pre-trend p=" `pp' "  t=-1: coef=" `bm1' " CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

* combo 5: no controls
display "=== Combo 5: no_ctrl ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 event_m1 event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus, absorb(county_code year) cluster(county_code)
test event_m5 event_m4 event_m3 event_m2
local pp = r(p)
local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
file write fcombo "5,no_ctrl,`pp',`bm1',`bm1'-1.96*`sm1',`bm1'+1.96*`sm1'" _n
display "Pre-trend p=" `pp' "  t=-1: coef=" `bm1' " CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

file close fcombo
display "Done"