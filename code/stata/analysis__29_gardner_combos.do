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

file open fcomb using "data/processed/gardner_combos.csv", write replace
file write fcomb "combo,controls,pre_p,t1_sig,post_sig_count" _n

* 不同控制变量组合
foreach ctrl in "primary_ratio secondary_ratio ln_pop gov_scale" ///
                 "primary_ratio secondary_ratio ln_pop" ///
                 "primary_ratio secondary_ratio gov_scale" ///
                 "primary_ratio secondary_ratio" ///
                 "secondary_ratio ln_pop gov_scale" ///
                 "ln_pop gov_scale" ///
                 "" {

    display "=== Combo: `ctrl' ==="

    cap did2s `yvar', ///
        first_stage(i.county_code i.year `ctrl') ///
        second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                     event_p1 event_p2 event_p3 event_p4 event_p5 ///
                     event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
        treatment(D2) ///
        cluster(county_code)

    if _rc != 0 {
        display "  Failed"
        continue
    }

    * 预趋势 F 检验
    test event_m5 event_m4 event_m3 event_m2
    local pre_p = r(p)

    * t=1 是否显著
    local b1 = _b[event_p1]
    local s1 = _se[event_p1]
    local t1_sig = 0
    if (`b1' - 1.96*`s1' > 0) | (`b1' + 1.96*`s1' < 0) local t1_sig = 1

    * 政策后显著期数
    local sig_cnt = 0
    foreach p in p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
        local bp = _b[event_`p']
        local sp = _se[event_`p']
        if (`bp' - 1.96*`sp' > 0) | (`bp' + 1.96*`sp' < 0) local sig_cnt = `sig_cnt' + 1
    }

    display "  Pre-p = `pre_p', t1_sig = `t1_sig', post_sig = `sig_cnt'/10"

    file write fcomb "`ctrl',`pre_p',`t1_sig',`sig_cnt'" _n
}

file close fcomb
display "Done"