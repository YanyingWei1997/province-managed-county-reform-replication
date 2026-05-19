clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T45: 路径 A — 用 D1-only 县作为对照组的三种规范
* (1) Restrict-control: D2-treated vs D1-only
* (2) Triple-DID: include D1 as additional regressor
* (3) Pure D1-only sub-sample TWFE (sanity check)
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T45: D1-only as alternative control"
display "=========================================="

* 标记 D2 处理状态
bysort county_code: egen d2_ever = max(D2)
bysort county_code: egen d1_ever = max(D1)

* D1-only：D1 处理过但从未 D2
gen byte d1_only_county = (d1_ever == 1 & d2_ever == 0)
* D2-treated（含同时 D1）
gen byte d2_treated_county = (d2_ever == 1)
* Never-treated
gen byte never_treated_county = (d1_ever == 0 & d2_ever == 0)

* 县总数统计
preserve
duplicates drop county_code, force
display "Total counties: " _N
quietly count if d2_treated_county == 1
display "  D2-treated: " r(N)
quietly count if d1_only_county == 1
display "  D1-only: " r(N)
quietly count if never_treated_county == 1
display "  Never-treated: " r(N)
restore

* ============================================================
* 1. 基准复现：D2-treated vs Never-treated（原 §4.2）
* ============================================================
display "========== Spec 1: D2 vs Never-treated (baseline reproduction) =========="
preserve
keep if d2_treated_county == 1 | never_treated_county == 1
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
local n1 = e(N)
display "  Baseline TWFE D2: " %6.3f `b1' " (SE " %6.3f `s1' ", p " %5.3f `p1' ", N=" `n1' ")"
restore

* ============================================================
* 2. 限制对照：D2-treated vs D1-only
* ============================================================
display "========== Spec 2: D2-treated vs D1-only =========="
preserve
keep if d2_treated_county == 1 | d1_only_county == 1
quietly count
display "  Sample obs: " r(N)
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local n2 = e(N)
display "  D2 vs D1-only TWFE: " %6.3f `b2' " (SE " %6.3f `s2' ", p " %5.3f `p2' ", N=" `n2' ")"
restore

* ============================================================
* 3. 全样本 + D1 作为额外控制变量
* ============================================================
display "========== Spec 3: Full sample, control for D1 indicator =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local n3 = e(N)
display "  D2 (control for D1) TWFE: " %6.3f `b3' " (SE " %6.3f `s3' ", p " %5.3f `p3' ", N=" `n3' ")"

* ============================================================
* 4. 三重交互：D2 × (D1-eligible) — 测试 D1-only 县反应是否不同
* ============================================================
display "========== Spec 4: D2 × D1-eligible interaction =========="
* D1-eligible: 该县曾接受过 D1（任何时点），即 d1_ever == 1
gen byte d1_eligible = d1_ever
gen byte d2_x_d1elig = D2 * d1_eligible

reghdfe `yvar' D2 d2_x_d1elig D1 `controls', absorb(county_code year) cluster(county_code)
local b4_d2 = _b[D2]
local s4_d2 = _se[D2]
local b4_int = _b[d2_x_d1elig]
local s4_int = _se[d2_x_d1elig]
display "  D2 main: " %6.3f `b4_d2' " (SE " %6.3f `s4_d2' ")"
display "  D2 × D1-eligible interaction: " %6.3f `b4_int' " (SE " %6.3f `s4_int' ")"
display "  D2 effect for D1-eligible counties: " %6.3f (`b4_d2' + `b4_int')
display "  D2 effect for D1-non-eligible counties: " %6.3f `b4_d2'

* ============================================================
* 5. CS-DID on D2 vs D1-only sub-sample
* ============================================================
display "========== Spec 5: CS-DID with D1-only as control =========="
preserve
keep if d2_treated_county == 1 | d1_only_county == 1
* Build gvar for D2
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)
sort county_code year

cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(drimp)
if _rc != 0 | e(N)==0 {
    display "  drimp failed, fallback to method(reg)"
    csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(reg)
}
csdid_estat simple
matrix res = r(table)
local b5 = res[1,1]
local s5 = res[2,1]
display "  CS-DID (D1-only control): " %6.3f `b5' " (SE " %6.3f `s5' ")"
restore

* ============================================================
* 6. 输出
* ============================================================
file open fout using "outputs/tables/table_d1only_control.csv", write replace
file write fout "spec,coef,se,p_value,N,note" _n
file write fout "TWFE_baseline_D2_vs_never,`b1',`s1',`p1',`n1',Baseline reproduction" _n
file write fout "TWFE_D2_vs_D1only,`b2',`s2',`p2',`n2',Restricted control: D2-treated vs D1-only" _n
file write fout "TWFE_full_with_D1_control,`b3',`s3',`p3',`n3',Full sample with D1 indicator" _n
file write fout "TWFE_D2_x_D1eligible,`b4_int',`s4_int',,,Interaction D2 × D1-eligible (in full sample with D1 control)" _n
file write fout "CSDID_D2_vs_D1only,`b5',`s5',,,CS-DID with D1-only control" _n
file close fout

display "=========================================="
display "T45 SUMMARY"
display "Spec 1 (baseline D2 vs never): " %6.3f `b1' " (p " %5.3f `p1' ")"
display "Spec 2 (D2 vs D1-only):        " %6.3f `b2' " (p " %5.3f `p2' ")"
display "Spec 3 (full + D1 control):    " %6.3f `b3' " (p " %5.3f `p3' ")"
display "Spec 4 (D2 × D1-eligible int): " %6.3f `b4_int' " (SE " %6.3f `s4_int' ")"
display "Spec 5 (CS-DID D2 vs D1-only): " %6.3f `b5' " (SE " %6.3f `s5' ")"
display "=========================================="
