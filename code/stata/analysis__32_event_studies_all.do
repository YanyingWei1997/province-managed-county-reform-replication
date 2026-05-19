clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which did2s
if _rc != 0 ssc install did2s

local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

file open fall using "data/processed/es_all_specs.csv", write replace
file write fall "spec,period,coef,ci_lower,ci_upper,se" _n

* 规格1: Gardner 全控制变量
display "=== Spec 1: Gardner (full controls) ==="
did2s `yvar', ///
    first_stage(i.county_code i.year primary_ratio secondary_ratio ln_pop gov_scale) ///
    second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                 event_p1 event_p2 event_p3 event_p4 event_p5 ///
                 event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
    treatment(D2) cluster(county_code)

foreach p in m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
    local b = _b[event_`p']
    local s = _se[event_`p']
    local lo = `b' - 1.96 * `s'
    local hi = `b' + 1.96 * `s'
    file write fall "full,`p',`b',`lo',`hi',`s'" _n
}

* 规格2: Gardner 无控制变量
display "=== Spec 2: Gardner (no controls) ==="
did2s `yvar', ///
    first_stage(i.county_code i.year) ///
    second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                 event_p1 event_p2 event_p3 event_p4 event_p5 ///
                 event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
    treatment(D2) cluster(county_code)

foreach p in m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
    local b = _b[event_`p']
    local s = _se[event_`p']
    local lo = `b' - 1.96 * `s'
    local hi = `b' + 1.96 * `s'
    file write fall "no_ctrl,`p',`b',`lo',`hi',`s'" _n
}

* 规格3: Gardner 仅产业结构
display "=== Spec 3: Gardner (industry only) ==="
did2s `yvar', ///
    first_stage(i.county_code i.year primary_ratio secondary_ratio) ///
    second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                 event_p1 event_p2 event_p3 event_p4 event_p5 ///
                 event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
    treatment(D2) cluster(county_code)

foreach p in m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
    local b = _b[event_`p']
    local s = _se[event_`p']
    local lo = `b' - 1.96 * `s'
    local hi = `b' + 1.96 * `s'
    file write fall "industry,`p',`b',`lo',`hi',`s'" _n
}

* 规格4: Sun-Abraham
display "=== Spec 4: Sun-Abraham ==="
cap which eventstudyinteract
if _rc != 0 ssc install eventstudyinteract

gen byte never_treat = (gvar == 0)

eventstudyinteract `yvar' ///
    event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 ///
    event_p6 event_p7 event_p8 event_p9 event_p10plus, ///
    cohort(gvar) control_cohort(never_treat) ///
    absorb(county_code year) ///
    vce(cluster county_code) ///
    covariates(primary_ratio secondary_ratio ln_pop gov_scale)

matrix B = e(b_iw)
matrix V = e(V_iw)

local i = 1
foreach p in m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
    local b = B[1, `i']
    local s = sqrt(V[`i',`i'])
    local lo = `b' - 1.96 * `s'
    local hi = `b' + 1.96 * `s'
    file write fall "sunab,`p',`b',`lo',`hi',`s'" _n
    local i = `i' + 1
}

file close fall
display "Saved: es_all_specs.csv"
display "Done"