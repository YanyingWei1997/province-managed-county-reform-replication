clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

* ============================================================
* A. 排除 t=-1 期：重新跑完整事件研究
* ============================================================
display "=== Exclude t=-1: full event study ==="
reghdfe `yvar' event_m5 event_m4 event_m3 event_m2 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 ///
    event_p6 event_p7 event_p8 event_p9 event_p10plus ///
    `controls', absorb(county_code year) cluster(county_code)

test event_m5 event_m4 event_m3 event_m2
display "Pre-trend F (excl m1): p = " r(p)

* 保存 CSV
file open fex using "data/processed/es_twfe_excl_m1.csv", write replace
file write fex "period,coef,ci_lower,ci_upper,se" _n
file write fex "0,0,0,0,0" _n

local periods "m5 m4 m3 m2 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums   "-5 -4 -3 -2 1 2 3 4 5 6 7 8 9 10"

local i = 1
foreach p of local periods {
    local pnum : word `i' of `pnums'
    local bval = _b[event_`p']
    local seval = _se[event_`p']
    local loval = `bval' - 1.96 * `seval'
    local hival = `bval' + 1.96 * `seval'
    file write fex "`pnum',`bval',`loval',`hival',`seval'" _n
    local i = `i' + 1
}
file close fex
display "Saved: es_twfe_excl_m1.csv"

* ============================================================
* B. 仅用 t=-6 到 t=-3 四期做预趋势检验（排除 t=-2, t=-1）
* ============================================================
display "=== Pre-trend: m6 m5 m4 m3 only ==="
reghdfe `yvar' event_m6 event_m5 event_m4 event_m3 event_p1 ///
    `controls', absorb(county_code year) cluster(county_code)
test event_m6 event_m5 event_m4 event_m3
display "Pre-trend F (m6-m3): p = " r(p)

* ============================================================
* C. 仅用 ln_gdppc 做事件研究（不依赖增长波动）
* ============================================================
local yvar2 "ln_gdppc"

display "=== Event study using ln_gdppc ==="
reghdfe `yvar2' event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 ///
    event_p6 event_p7 event_p8 event_p9 event_p10plus ///
    `controls', absorb(county_code year) cluster(county_code)

test event_m5 event_m4 event_m3 event_m2
display "ln_gdppc pre-trend F: p = " r(p)

local bm1 = _b[event_m1]
local sm1 = _se[event_m1]
display "ln_gdppc t=-1: coef=`bm1' CI=[" `bm1'-1.96*`sm1' "," `bm1'+1.96*`sm1' "]"

display "27 done"