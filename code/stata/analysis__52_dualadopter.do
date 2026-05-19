clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T52: 双采纳县（D1+D2 dual-adopter）编码检验
* 关切：218 个双采纳县在 CS-DID 下其 D2 cohort 年份可能取自 D1_year
*   (§3.1 文字 "earlier of the two reform years" → 误把 D1 启动年作 D2 启动年)
* 检验：把双采纳县剔除，重做 TWFE 与 CS-DID，看 1.192 (CS-DID) 是否被推动。
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* ----- 标记双采纳县（D1_year 与 D2_year 都非缺失） -----
gen has_d1 = !missing(D1_year)
gen has_d2 = !missing(D2_year)
gen dual = has_d1 & has_d2

* 县级标记
bysort county_code: egen ever_dual = max(dual)
preserve
    keep county_code ever_dual
    duplicates drop
    tab ever_dual
    count if ever_dual == 1
    display "  双采纳县总数（county-level） = " r(N)
restore

display "=========================================="
display "T52: Dual-adopter encoding check"
display "=========================================="

* ----- 全样本基准 -----
display "========== Spec 1: Full sample baseline (Table 1 headline) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
local n1 = e(N)
display "  D2 = " %6.4f `b1' "  (SE " %6.4f `s1' ", p " %5.3f `p1' ", N=" `n1' ")"

* ----- 剔除双采纳县 -----
display "========== Spec 2: Drop 218 dual-adopters =========="
preserve
keep if ever_dual == 0
quietly tab county_code
local n_cnty_drop = r(r)
display "  剩余县数 = " `n_cnty_drop'
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local n2 = e(N)
display "  D2 = " %6.4f `b2' "  (SE " %6.4f `s2' ", p " %5.3f `p2' ", N=" `n2' ")"
restore

* ----- D2-only 子样本（D2 处理 + 从未处理） -----
display "========== Spec 3: D2-only treated + Never-treated (excludes D1-only and dual) =========="
preserve
keep if (has_d2 == 1 & has_d1 == 0) | (has_d1 == 0 & has_d2 == 0)
quietly tab county_code
local n_cnty_3 = r(r)
display "  样本县数 = " `n_cnty_3'
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local n3 = e(N)
display "  D2 = " %6.4f `b3' "  (SE " %6.4f `s3' ", p " %5.3f `p3' ", N=" `n3' ")"
restore

* ----- CS-DID on D2-only sample (drop dual-adopters) -----
display "========== Spec 4: CS-DID on D2-only treated + never-treated =========="
preserve
keep if (has_d2 == 1 & has_d1 == 0) | (has_d1 == 0 & has_d2 == 0)
gen first_treat = D2_year
replace first_treat = 0 if missing(first_treat)
cap which csdid
if _rc {
    cap ssc install csdid, replace
    cap ssc install drdid, replace
}
cap noi csdid `yvar' `controls', ivar(county_code) time(year) gvar(first_treat) agg(simple)
if _rc == 0 {
    matrix b = e(b)
    matrix V = e(V)
    local b4 = b[1,1]
    local s4 = sqrt(V[1,1])
    local p4 = 2*(1 - normal(abs(`b4'/`s4')))
    local n4 = e(N)
    display "  CS-DID D2 (D2-only sample) = " %6.4f `b4' "  (SE " %6.4f `s4' ", p " %5.3f `p4' ", N=" `n4' ")"
}
else {
    local b4 = .
    local s4 = .
    local p4 = .
    local n4 = .
    display "  csdid failed; rc = " _rc
}
restore

* ----- CS-DID on full sample (current Table 1 headline) -----
display "========== Spec 5: CS-DID on full sample (current Table 1) =========="
preserve
gen first_treat = D2_year
replace first_treat = 0 if missing(first_treat)
cap noi csdid `yvar' `controls', ivar(county_code) time(year) gvar(first_treat) agg(simple)
if _rc == 0 {
    matrix b = e(b)
    matrix V = e(V)
    local b5 = b[1,1]
    local s5 = sqrt(V[1,1])
    local p5 = 2*(1 - normal(abs(`b5'/`s5')))
    local n5 = e(N)
    display "  CS-DID D2 (full sample) = " %6.4f `b5' "  (SE " %6.4f `s5' ", p " %5.3f `p5' ", N=" `n5' ")"
}
else {
    local b5 = .
    local s5 = .
    local p5 = .
    local n5 = .
    display "  csdid failed; rc = " _rc
}
restore

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t52_dualadopter.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,n_obs,note" _n
file write fout "1_full_baseline_TWFE,`b1',`s1',`p1',`n1',Full-sample joint TWFE (Table 1 headline)" _n
file write fout "2_drop_dual_TWFE,`b2',`s2',`p2',`n2',TWFE excluding 218 dual-adopters" _n
file write fout "3_d2only_+never_TWFE,`b3',`s3',`p3',`n3',TWFE on D2-only treated + never-treated" _n
file write fout "4_d2only_CSDID,`b4',`s4',`p4',`n4',CS-DID on D2-only treated + never-treated" _n
file write fout "5_full_CSDID,`b5',`s5',`p5',`n5',CS-DID on full sample (current Table 1)" _n
file close fout

display "=========================================="
display "T52 SUMMARY"
display "  Full TWFE (joint D1+D2):       D2 = " %6.4f `b1' "  (p " %5.3f `p1' ", N " %9.0f `n1' ")"
display "  TWFE drop dual-adopters:       D2 = " %6.4f `b2' "  (p " %5.3f `p2' ", N " %9.0f `n2' ")"
display "  TWFE D2-only + never-treated:  D2 = " %6.4f `b3' "  (p " %5.3f `p3' ", N " %9.0f `n3' ")"
display "  CS-DID D2-only + never-treated:D2 = " %6.4f `b4' "  (p " %5.3f `p4' ", N " %9.0f `n4' ")"
display "  CS-DID full sample (Table 1):  D2 = " %6.4f `b5' "  (p " %5.3f `p5' ", N " %9.0f `n5' ")"
display "=========================================="
