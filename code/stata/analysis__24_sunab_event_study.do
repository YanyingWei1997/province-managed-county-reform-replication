clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools
cap which eventstudyinteract
if _rc != 0 ssc install eventstudyinteract
cap which avar
if _rc != 0 ssc install avar

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local yvar     "gdp_growth"

* gvar: year of first D2 treatment (0 = never treated)
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

gen byte never_treat = (gvar == 0)

* ============================================================
* Sun & Abraham (2021) interaction-weighted estimator
* ============================================================
eventstudyinteract `yvar' ///
    event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 ///
    event_p6 event_p7 event_p8 event_p9 event_p10plus, ///
    cohort(gvar) control_cohort(never_treat) ///
    absorb(county_code year) ///
    vce(cluster county_code) ///
    covariates(`controls')

* ── 平行趋势：从 e(b_iw) e(V_iw) 读取 ──────────────────
matrix B = e(b_iw)
matrix V = e(V_iw)

* Joint chi2 test for pre-trend (cols 1-4: m5 m4 m3 m2)
matrix Bpre   = B[1, 1..4]
matrix Vpre   = V[1..4, 1..4]
matrix chi2m  = Bpre * inv(Vpre) * Bpre'
local chi2val = chi2m[1,1]
local pval    = chi2tail(4, `chi2val')
display "Sun-Abraham pre-trend chi2(4) = " `chi2val' "  p = " `pval'

* ── 保存逐期系数 CSV ─────────────────────────────────────
local periods "m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums   "-5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"
local nc = colsof(B)
display "Sun-AB cols: `nc'"

file open fsa using "data/processed/es_sunab.csv", write replace
file write fsa "period,coef,se,ci_lower,ci_upper" _n
file write fsa "0,0,0,0,0" _n

local i = 1
foreach p of local periods {
    local pnum : word `i' of `pnums'
    local bval = B[1, `i']
    local seval = sqrt(V[`i', `i'])
    local loval = `bval' - 1.96 * `seval'
    local hival = `bval' + 1.96 * `seval'
    file write fsa "`pnum',`bval',`loval',`hival',`seval'" _n
    local i = `i' + 1
}
file close fsa
display "Saved: es_sunab.csv"

* ── 顺带输出 ATT 到 table_sdid.csv 追加 ─────────────────
* 加权平均 ATT（所有 post 期均值）
local np = 10
local att_sum = 0
forvalues j = 6/15 {
    local att_sum = `att_sum' + B[1, `j']
}
local att_avg = `att_sum' / `np'
display "Sun-AB avg ATT (post periods) = `att_avg'"

display "24 done"
