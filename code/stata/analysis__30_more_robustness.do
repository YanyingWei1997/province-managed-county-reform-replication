clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which did2s
if _rc != 0 ssc install did2s

* gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

file open fout using "data/processed/robustness_check.csv", write replace
file write fout "spec,yvar,pre_all_pass,t1_sig,post_sig_count" _n

* A. 不同结果变量
foreach yv in "gdp_growth" "ln_gdppc" "fiscal_autonomy" "ln_fiscal_rev_pc" {

    display "=== `yv' ==="

    cap did2s `yv' primary_ratio secondary_ratio ln_pop gov_scale, ///
        first_stage(i.county_code i.year) ///
        second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                     event_p1 event_p2 event_p3 event_p4 event_p5 ///
                     event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
        treatment(D2) cluster(county_code)

    if _rc != 0 {
        file write fout "`yv',`yv',.,.,." _n
        continue
    }

    test event_m5 event_m4 event_m3 event_m2
    local pre_p = r(p)

    local t1_sig = 0
    local b1 = _b[event_p1]
    local s1 = _se[event_p1]
    if (`b1' - 1.96*`s1' > 0) | (`b1' + 1.96*`s1' < 0) local t1_sig = 1

    local sig_cnt = 0
    foreach p in p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
        local bp = _b[event_`p']
        local sp = _se[event_`p']
        if (`bp' - 1.96*`sp' > 0) | (`bp' + 1.96*`sp' < 0) local sig_cnt = `sig_cnt' + 1
    }

    display "  pre_p=`pre_p', t1_sig=`t1_sig', post_sig=`sig_cnt'"
    file write fout "`yv',`yv',`pre_p',`t1_sig',`sig_cnt'" _n
}

* B. 不同聚类标准误
display "=== Clustering ==="

cap did2s gdp_growth primary_ratio secondary_ratio ln_pop gov_scale, ///
    first_stage(i.county_code i.year) ///
    second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                 event_p1 event_p2 event_p3 event_p4 event_p5) ///
    treatment(D2) cluster(county_code)

test event_m5 event_m4 event_m3 event_m2
local pre_p = r(p)

local t1_sig = 0
local b1 = _b[event_p1]
local s1 = _se[event_p1]
if (`b1' - 1.96*`s1' > 0) | (`b1' + 1.96*`s1' < 0) local t1_sig = 1

local sig_cnt = 0
foreach p in p1 p2 p3 p4 p5 {
    local bp = _b[event_`p']
    local sp = _se[event_`p']
    if (`bp' - 1.96*`sp' > 0) | (`bp' + 1.96*`sp' < 0) local sig_cnt = `sig_cnt' + 1
}

display "  pre_p=`pre_p', t1_sig=`t1_sig', post_sig=`sig_cnt'"
file write fout "cluster_county,county,`pre_p',`t1_sig',`sig_cnt'" _n

file close fout
display "Done"