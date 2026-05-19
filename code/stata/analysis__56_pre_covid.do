clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T56: COVID 期截断稳健性
* 关切：样本含 2020-2023 共 4 年疫情冲击（占 17%）。D2 推进
*   基本到 2019 结束，疫情对 D2 vs 非 D2 县的财政纾困分配可能不对称。
* 检验：把样本截至 2019，重做头条 TWFE 与 CS-DID。
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T56: Pre-COVID truncation (2000-2019 only)"
display "=========================================="

* ----- Spec 1: 全样本基准（参照） -----
display "========== Spec 1: Full sample 2000-2023 (Table 1 headline) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
local n1 = e(N)
display "  D2 = " %6.4f `b1' "  (SE " %6.4f `s1' ", p " %5.3f `p1' ", N=" `n1' ")"

* ----- Spec 2: 截至 2019（pre-COVID） -----
display "========== Spec 2: Truncated to 2000-2019 =========="
preserve
keep if year <= 2019
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local n2 = e(N)
display "  D2 = " %6.4f `b2' "  (SE " %6.4f `s2' ", p " %5.3f `p2' ", N=" `n2' ")"
restore

* ----- Spec 3: 截至 2018（更保守，移除 2019 边界年） -----
display "========== Spec 3: Truncated to 2000-2018 =========="
preserve
keep if year <= 2018
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local n3 = e(N)
display "  D2 = " %6.4f `b3' "  (SE " %6.4f `s3' ", p " %5.3f `p3' ", N=" `n3' ")"
restore

* ----- Spec 4: 仅 2020-2023（疫情期效应） -----
display "========== Spec 4: COVID-only 2020-2023 =========="
preserve
keep if year >= 2020
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b4 = _b[D2]
local s4 = _se[D2]
local p4 = 2*(1 - normal(abs(`b4'/`s4')))
local n4 = e(N)
display "  D2 = " %6.4f `b4' "  (SE " %6.4f `s4' ", p " %5.3f `p4' ", N=" `n4' ")"
restore

* ----- Spec 5: CS-DID 截至 2019 -----
display "========== Spec 5: CS-DID truncated to 2000-2019 =========="
preserve
keep if year <= 2019
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
    local b5 = b[1,1]
    local s5 = sqrt(V[1,1])
    local p5 = 2*(1 - normal(abs(`b5'/`s5')))
    local n5 = e(N)
    display "  CS-DID D2 (pre-COVID) = " %6.4f `b5' "  (SE " %6.4f `s5' ", p " %5.3f `p5' ", N=" `n5' ")"
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
file open fout using "outputs/tables/table_t56_pre_covid.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,n_obs,note" _n
file write fout "1_full_sample_2000_2023,`b1',`s1',`p1',`n1',Full sample (Table 1 headline)" _n
file write fout "2_pre_covid_2000_2019,`b2',`s2',`p2',`n2',Pre-COVID truncation 2000-2019" _n
file write fout "3_pre_covid_2000_2018,`b3',`s3',`p3',`n3',Pre-COVID truncation 2000-2018" _n
file write fout "4_covid_only_2020_2023,`b4',`s4',`p4',`n4',COVID-only window 2020-2023" _n
file write fout "5_csdid_pre_covid,`b5',`s5',`p5',`n5',CS-DID truncated to 2000-2019" _n
file close fout

display "=========================================="
display "T56 SUMMARY"
display "  Full 2000-2023 TWFE:        D2 = " %6.4f `b1' " (p " %5.3f `p1' ", N " %9.0f `n1' ")"
display "  Pre-COVID 2000-2019 TWFE:   D2 = " %6.4f `b2' " (p " %5.3f `p2' ", N " %9.0f `n2' ")"
display "  Pre-COVID 2000-2018 TWFE:   D2 = " %6.4f `b3' " (p " %5.3f `p3' ", N " %9.0f `n3' ")"
display "  COVID 2020-2023 TWFE:       D2 = " %6.4f `b4' " (p " %5.3f `p4' ", N " %9.0f `n4' ")"
display "  Pre-COVID CS-DID:           D2 = " %6.4f `b5' " (p " %5.3f `p5' ", N " %9.0f `n5' ")"
display "=========================================="
