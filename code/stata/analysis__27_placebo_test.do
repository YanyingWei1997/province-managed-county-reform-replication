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

file open fplc using "data/processed/es_placebo.csv", write replace
file write fplc "fake_year,n,coef_m5,se_m5,p_m5,coef_m2,se_m2,p_m2,att,att_p" _n

* placebo: 假设改革发生在 t-2, t-3, t-4, t-5
foreach fake in 2 3 4 5 {
    display "=== Placebo year: actual - `fake' ==="

    * 构建 fake treatment indicator
    cap drop fake_D fake_event*
    gen fake_D = (D2_year - year >= `fake')
    replace fake_D = 0 if gvar == 0  // never-treated = 0

    * fake event time dummies relative to fake treatment
    gen fake_et_m5 = 0
    gen fake_et_m2 = 0
    gen fake_et_0  = 0
    gen fake_et_p2 = 0

    replace fake_et_m5 = 1 if fake_D == 1 & (year == gvar - `fake' - 5)
    replace fake_et_m2 = 1 if fake_D == 1 & (year == gvar - `fake' - 2)
    replace fake_et_0  = 1 if fake_D == 1 & (year == gvar - `fake')
    replace fake_et_p2 = 1 if fake_D == 1 & (year == gvar - `fake' + 2)

    count if fake_D == 1
    local nn = r(N)

    reghdfe `yvar' fake_et_m5 fake_et_m2 fake_et_p2 ///
        `controls', absorb(county_code year) cluster(county_code)

    local bm5  = _b[fake_et_m5]
    local sm5  = _se[fake_et_m5]
    local pm5  = 2*normal(-abs(`bm5'/`sm5'))
    local bm2  = _b[fake_et_m2]
    local sm2  = _se[fake_et_m2]
    local pm2  = 2*normal(-abs(`bm2'/`sm2'))
    local bp2  = _b[fake_et_p2]
    local sp2  = _se[fake_et_p2]
    local pp2  = 2*normal(-abs(`bp2'/`sp2'))

    display "  m5: coef=`bm5' p=`pm5'"
    display "  m2: coef=`bm2' p=`pm2'"
    display "  p2: coef=`bp2' p=`pp2'"

    file write fplc "`fake',`nn',`bm5',`sm5',`pm5',`bm2',`sm2',`pm2',`bp2',`pp2'" _n
}

file close fplc
display "Placebo done"