clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which did2s
if _rc != 0 ssc install did2s

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar     "gdp_growth"

* ============================================================
* Gardner (2021) two-stage DID
* first_stage:  unit + time FE + controls on untreated obs
* second_stage: event-study dummies
* treatment:    D2 (binary treatment indicator)
* ============================================================
did2s `yvar', ///
    first_stage(i.county_code i.year `controls') ///
    second_stage(event_m5 event_m4 event_m3 event_m2 event_m1 ///
                 event_p1 event_p2 event_p3 event_p4 event_p5 ///
                 event_p6 event_p7 event_p8 event_p9 event_p10plus) ///
    treatment(D2) ///
    cluster(county_code)

* ── 平行趋势联合检验（m5 m4 m3 m2）─────────────────────────
test event_m5 event_m4 event_m3 event_m2
display "Gardner pre-trend F(" r(df) "," r(df_r) ")=" r(F) "  p=" r(p)

* ── 保存逐期系数 CSV ─────────────────────────────────────
local periods "m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums   "-5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"

file open fg2s using "data/processed/es_did2s.csv", write replace
file write fg2s "period,coef,ci_lower,ci_upper,se" _n
file write fg2s "0,0,0,0,0" _n

local i = 1
foreach p of local periods {
    local pnum : word `i' of `pnums'
    local bval = _b[event_`p']
    local seval = _se[event_`p']
    local loval = `bval' - 1.96*`seval'
    local hival = `bval' + 1.96*`seval'
    file write fg2s "`pnum',`bval',`loval',`hival',`seval'" _n
    local i = `i' + 1
}
file close fg2s
display "Saved: es_did2s.csv"

* ── ATT 整体均值（post 期平均）用于 forest plot ───────────
local att_sum = 0
foreach p in p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus {
    local att_sum = `att_sum' + _b[event_`p']
}
local att_avg = `att_sum' / 10
display "Gardner avg ATT = " `att_avg'

display "25 done"
