clear all
set more off
cd "."
* ============================================================
* T34: 面板层面 D2 异质性 (子组 TWFE/CS-DID + 交互 TWFE)
* 把异质性识别从仅探索性的 GRF 转到面板因果识别框架
* ============================================================

* ============================================================
* 0. 把 fiscal_autonomy_pre 从截面 CSV 合并回面板
* ============================================================
import delimited "data/processed/grf_input.csv", clear
keep county_code fiscal_autonomy_pre
duplicates drop county_code, force
tempfile fa_pre
save `fa_pre'

use "data/analysis/panel_analysis_public.dta", clear
merge m:1 county_code using `fa_pre', keep(master match) nogen

* 构造改革前财政自主度四分位
* 仅基于 fiscal_autonomy_pre 非缺失的县
quietly summarize fiscal_autonomy_pre, detail
local p25 = r(p25)
local p50 = r(p50)
local p75 = r(p75)
display "fa_pre quartiles: p25=" `p25' ", p50=" `p50' ", p75=" `p75'

gen byte fa_q1 = (fiscal_autonomy_pre <= `p25') if !missing(fiscal_autonomy_pre)
gen byte fa_q2 = (fiscal_autonomy_pre > `p25' & fiscal_autonomy_pre <= `p50') if !missing(fiscal_autonomy_pre)
gen byte fa_q3 = (fiscal_autonomy_pre > `p50' & fiscal_autonomy_pre <= `p75') if !missing(fiscal_autonomy_pre)
gen byte fa_q4 = (fiscal_autonomy_pre > `p75') if !missing(fiscal_autonomy_pre)

label variable fa_q1 "fiscal_autonomy_pre Q1 (lowest)"
label variable fa_q4 "fiscal_autonomy_pre Q4 (highest)"

* 检查分组合理性
quietly count if fa_q1 == 1 & year == 2000
display "Q1 counties: " r(N)
quietly count if fa_q4 == 1 & year == 2000
display "Q4 counties: " r(N)

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 输出文件初始化
file open fout using "outputs/tables/table_d2_heterogeneity_panel.csv", write replace
file write fout "spec,subgroup,coef,se,ci_lower,ci_upper,p,N" _n

* ============================================================
* 1. 子组 TWFE: D2 effect within each fa_pre quartile
* ============================================================
display "========== 子组 TWFE D2 (each fa_pre quartile) =========="

forvalues q = 1/4 {
    display "---- Q`q' ----"
    preserve
    keep if fa_q`q' == 1

    quietly count
    display "Q`q' obs: " r(N)

    cap reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
    if _rc == 0 {
        local q`q'_coef = _b[D2]
        local q`q'_se   = _se[D2]
        local q`q'_p    = 2 * (1 - normal(abs(`q`q'_coef'/`q`q'_se')))
        local q`q'_lo   = `q`q'_coef' - 1.96 * `q`q'_se'
        local q`q'_hi   = `q`q'_coef' + 1.96 * `q`q'_se'
        local q`q'_n    = e(N)

        display "TWFE Q`q' D2: coef=`q`q'_coef', SE=`q`q'_se', p=`q`q'_p'"

        file write fout "TWFE_subgroup,Q`q'_fa,`q`q'_coef',`q`q'_se',`q`q'_lo',`q`q'_hi',`q`q'_p',`q`q'_n'" _n
    }
    else {
        display "Q`q' regression failed"
    }
    restore
}

* ============================================================
* 2. CS-DID for Q1 and Q4 subgroups
* ============================================================
display "========== CS-DID D2 (Q1 and Q4 subgroups) =========="

* 准备 gvar
bysort county_code: egen gvar_max = max(D2_year)
gen int gvar = int(gvar_max)
drop gvar_max
replace gvar = 0 if missing(gvar)
replace gvar = 0 if gvar < 2000

foreach q in 1 4 {
    display "---- CS-DID Q`q' ----"
    preserve
    keep if fa_q`q' == 1
    keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
        & !missing(ln_pop) & !missing(gov_scale)
    sort county_code year

    quietly count
    display "Q`q' CS-DID sample: " r(N)
    local csdid_q`q'_n = r(N)

    cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(drimp)
    if _rc != 0 | e(N)==0 {
        display "drimp failed for Q`q', try method(reg)"
        cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(reg)
    }
    if _rc == 0 {
        csdid_estat simple
        matrix res = r(table)
        local csdid_q`q'_coef = res[1,1]
        local csdid_q`q'_se   = res[2,1]
        local csdid_q`q'_lo   = res[5,1]
        local csdid_q`q'_hi   = res[6,1]

        display "CS-DID Q`q' D2: coef=`csdid_q`q'_coef', SE=`csdid_q`q'_se'"

        file write fout "CSDID_subgroup,Q`q'_fa,`csdid_q`q'_coef',`csdid_q`q'_se',`csdid_q`q'_lo',`csdid_q`q'_hi',,`csdid_q`q'_n'" _n
    }
    restore
}

* ============================================================
* 3. 面板交互 TWFE: D2 + D2*fa_q1 + D2*fa_q4
* ============================================================
display "========== Panel TWFE Interaction =========="

* 中间组 (Q2+Q3) 作为参照
gen D2_q1 = D2 * fa_q1
gen D2_q4 = D2 * fa_q4

label variable D2_q1 "D2 x Q1 (low fa)"
label variable D2_q4 "D2 x Q4 (high fa)"

reghdfe `yvar' D2 D2_q1 D2_q4 `controls', absorb(county_code year) cluster(county_code)

local int_d2_coef = _b[D2]
local int_d2_se   = _se[D2]
local int_d2_p    = 2 * (1 - normal(abs(`int_d2_coef'/`int_d2_se')))
local int_d2_lo   = `int_d2_coef' - 1.96 * `int_d2_se'
local int_d2_hi   = `int_d2_coef' + 1.96 * `int_d2_se'

local int_q1_coef = _b[D2_q1]
local int_q1_se   = _se[D2_q1]
local int_q1_p    = 2 * (1 - normal(abs(`int_q1_coef'/`int_q1_se')))
local int_q1_lo   = `int_q1_coef' - 1.96 * `int_q1_se'
local int_q1_hi   = `int_q1_coef' + 1.96 * `int_q1_se'

local int_q4_coef = _b[D2_q4]
local int_q4_se   = _se[D2_q4]
local int_q4_p    = 2 * (1 - normal(abs(`int_q4_coef'/`int_q4_se')))
local int_q4_lo   = `int_q4_coef' - 1.96 * `int_q4_se'
local int_q4_hi   = `int_q4_coef' + 1.96 * `int_q4_se'

local int_n = e(N)

display "Interaction D2 (Q2+Q3 ref): coef=`int_d2_coef', SE=`int_d2_se', p=`int_d2_p'"
display "Interaction D2*Q1:         coef=`int_q1_coef', SE=`int_q1_se', p=`int_q1_p'"
display "Interaction D2*Q4:         coef=`int_q4_coef', SE=`int_q4_se', p=`int_q4_p'"

file write fout "TWFE_interaction,D2_main_Q23ref,`int_d2_coef',`int_d2_se',`int_d2_lo',`int_d2_hi',`int_d2_p',`int_n'" _n
file write fout "TWFE_interaction,D2xQ1,`int_q1_coef',`int_q1_se',`int_q1_lo',`int_q1_hi',`int_q1_p',`int_n'" _n
file write fout "TWFE_interaction,D2xQ4,`int_q4_coef',`int_q4_se',`int_q4_lo',`int_q4_hi',`int_q4_p',`int_n'" _n

* Implied total D2 effect within each quartile
local q1_implied = `int_d2_coef' + `int_q1_coef'
local q4_implied = `int_d2_coef' + `int_q4_coef'
display "Implied total D2 in Q1: " `q1_implied'
display "Implied total D2 in Q4: " `q4_implied'

* Test: Q1 - Q4 (heterogeneity test)
test D2_q1 = D2_q4
local het_F = r(F)
local het_p = r(p)
display "Heterogeneity test (D2*Q1 = D2*Q4): F=`het_F', p=`het_p'"

file write fout "Heterogeneity_test,Q1_vs_Q4,,,,,`het_p'," _n

file close fout

display "========================================="
display "T34 SUMMARY"
display "Subgroup TWFE D2:  Q1=`q1_coef', Q2=`q2_coef', Q3=`q3_coef', Q4=`q4_coef'"
display "Subgroup CS-DID:   Q1=`csdid_q1_coef', Q4=`csdid_q4_coef'"
display "Interaction TWFE:  D2=`int_d2_coef', D2*Q1=`int_q1_coef', D2*Q4=`int_q4_coef'"
display "Heterogeneity test (Q1=Q4): p=`het_p'"
display "========================================="
