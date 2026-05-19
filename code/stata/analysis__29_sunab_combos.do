clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which eventstudyinteract
if _rc != 0 ssc install eventstudyinteract

local yvar "gdp_growth"

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000
gen byte never_treat = (gvar == 0)

file open fcomb using "data/processed/sunab_combos.csv", write replace
file write fcomb "combo,controls,t1_coef,t1_se,t1_ci_lo,t1_ci_hi,t1_sig,post_sig_count" _n

* 不同控制变量组合
foreach ctrl in "primary_ratio secondary_ratio ln_pop gov_scale" ///
                 "primary_ratio secondary_ratio ln_pop" ///
                 "primary_ratio secondary_ratio" ///
                 "" {

    display "=== Sun-Abraham: `ctrl' ==="

    cap eventstudyinteract `yvar' ///
        event_m5 event_m4 event_m3 event_m2 event_m1 ///
        event_p1 event_p2 event_p3 event_p4 event_p5 ///
        event_p6 event_p7 event_p8 event_p9 event_p10plus, ///
        cohort(gvar) control_cohort(never_treat) ///
        absorb(county_code year) ///
        vce(cluster county_code) ///
        covariates(`ctrl')

    if _rc != 0 {
        display "  Failed"
        continue
    }

    matrix B = e(b_iw)
    matrix V = e(V_iw)

    * t=1 系数
    local b1 = B[1, 6]
    local s1 = sqrt(V[6,6])
    local ci_lo1 = `b1' - 1.96*`s1'
    local ci_hi1 = `b1' + 1.96*`s1'
    local t1_sig = 0
    if (`ci_lo1' > 0) | (`ci_hi1' < 0) local t1_sig = 1

    * 政策后显著期数 (post periods 6-15)
    local sig_cnt = 0
    forvalues j = 6/15 {
        local bj = B[1, `j']
        local sj = sqrt(V[`j',`j'])
        if (`bj' - 1.96*`sj' > 0) | (`bj' + 1.96*`sj' < 0) local sig_cnt = `sig_cnt' + 1
    }

    display "  t1: coef=`b1', CI=[`ci_lo1', `ci_hi1'], sig=`t1_sig', post_sig=`sig_cnt'/10"

    file write fcomb "`ctrl',`ctrl',`b1',`s1',`ci_lo1',`ci_hi1',`t1_sig',`sig_cnt'" _n
}

file close fcomb
display "Done"