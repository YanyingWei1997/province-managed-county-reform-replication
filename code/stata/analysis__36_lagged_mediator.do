clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T36: 滞后中介稳健性
* 用 L1 中介替代当期中介，缓解中介与结果的同期内生性
* ============================================================

local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T36: Lagged mediator robustness"
display "=========================================="

* 设置 panel 结构
xtset county_code year

* 构造滞后一期中介
gen ln_fiscal_exp_pc_L1 = L.ln_fiscal_exp_pc
gen fiscal_autonomy_L1 = L.fiscal_autonomy

* 检查样本量
quietly count if !missing(gdp_growth_pc) & !missing(ln_fiscal_exp_pc_L1) & !missing(D2)
display "Sample with L1 fiscal_exp: " r(N)

quietly count if !missing(gdp_growth_pc) & !missing(fiscal_autonomy_L1) & !missing(D2)
display "Sample with L1 fiscal_autonomy: " r(N)

file open fout using "outputs/tables/table_lagged_mediator.csv", write replace
file write fout "spec,mediator,coef,se,ci_lower,ci_upper,p,N" _n

* ============================================================
* 1. Path 2 lagged: D2 -> L.ln_fiscal_exp_pc -> gdp_growth_pc
* ============================================================
display "========== Path 2 (lagged): Step 1 D2 -> L.ln_fiscal_exp_pc =========="
reghdfe ln_fiscal_exp_pc D2 `controls', absorb(county_code year) cluster(county_code)
local p2_g_coef = _b[D2]
local p2_g_se = _se[D2]
local p2_g_p = 2*(1 - normal(abs(`p2_g_coef'/`p2_g_se')))
local p2_g_lo = `p2_g_coef' - 1.96*`p2_g_se'
local p2_g_hi = `p2_g_coef' + 1.96*`p2_g_se'
display "γ (D2 -> ln_fiscal_exp_pc current): " `p2_g_coef' " (SE=" `p2_g_se' ")"
file write fout "Path2_step1_current,ln_fiscal_exp_pc,`p2_g_coef',`p2_g_se',`p2_g_lo',`p2_g_hi',`p2_g_p'," _n

display "========== Path 2 (lagged): Step 2 L.ln_fiscal_exp_pc -> gdp_growth (control D2) =========="
reghdfe gdp_growth_pc D2 ln_fiscal_exp_pc_L1 `controls', absorb(county_code year) cluster(county_code)
local p2_dL1 = _b[ln_fiscal_exp_pc_L1]
local p2_dL1_se = _se[ln_fiscal_exp_pc_L1]
local p2_dL1_p = 2*(1 - normal(abs(`p2_dL1'/`p2_dL1_se')))
local p2_dL1_lo = `p2_dL1' - 1.96*`p2_dL1_se'
local p2_dL1_hi = `p2_dL1' + 1.96*`p2_dL1_se'
local p2_dL1_n = e(N)
display "δ (L.ln_fiscal_exp_pc -> gdp_growth | D2): " `p2_dL1' " (SE=" `p2_dL1_se' ")"
file write fout "Path2_step2_lagged,L1_ln_fiscal_exp_pc,`p2_dL1',`p2_dL1_se',`p2_dL1_lo',`p2_dL1_hi',`p2_dL1_p',`p2_dL1_n'" _n

* Indirect effect = γ × δ_L1
local p2_indirect = `p2_g_coef' * `p2_dL1'
display "Path 2 indirect effect (lagged δ): " `p2_indirect'

* ============================================================
* 2. Path 1 lagged: D2 -> L.fiscal_autonomy -> gdp_growth_pc
* ============================================================
display "========== Path 1 (lagged): Step 1 D2 -> fiscal_autonomy current =========="
reghdfe fiscal_autonomy D2 `controls', absorb(county_code year) cluster(county_code)
local p1_a_coef = _b[D2]
local p1_a_se = _se[D2]
local p1_a_p = 2*(1 - normal(abs(`p1_a_coef'/`p1_a_se')))
local p1_a_lo = `p1_a_coef' - 1.96*`p1_a_se'
local p1_a_hi = `p1_a_coef' + 1.96*`p1_a_se'
display "α (D2 -> fiscal_autonomy current): " `p1_a_coef' " (SE=" `p1_a_se' ")"
file write fout "Path1_step1_current,fiscal_autonomy,`p1_a_coef',`p1_a_se',`p1_a_lo',`p1_a_hi',`p1_a_p'," _n

display "========== Path 1 (lagged): Step 2 L.fiscal_autonomy -> gdp_growth (control D2) =========="
reghdfe gdp_growth_pc D2 fiscal_autonomy_L1 `controls', absorb(county_code year) cluster(county_code)
local p1_bL1 = _b[fiscal_autonomy_L1]
local p1_bL1_se = _se[fiscal_autonomy_L1]
local p1_bL1_p = 2*(1 - normal(abs(`p1_bL1'/`p1_bL1_se')))
local p1_bL1_lo = `p1_bL1' - 1.96*`p1_bL1_se'
local p1_bL1_hi = `p1_bL1' + 1.96*`p1_bL1_se'
local p1_bL1_n = e(N)
display "β (L.fiscal_autonomy -> gdp_growth | D2): " `p1_bL1' " (SE=" `p1_bL1_se' ")"
file write fout "Path1_step2_lagged,L1_fiscal_autonomy,`p1_bL1',`p1_bL1_se',`p1_bL1_lo',`p1_bL1_hi',`p1_bL1_p',`p1_bL1_n'" _n

local p1_indirect = `p1_a_coef' * `p1_bL1'
display "Path 1 indirect effect (lagged β): " `p1_indirect'

file close fout

display "=========================================="
display "T36 SUMMARY"
display "Path 1: α (D2->fa) = `p1_a_coef', β (L.fa->growth) = `p1_bL1'"
display "        Indirect (lagged) = `p1_indirect'"
display "Path 2: γ (D2->ln_exp) = `p2_g_coef', δ (L.ln_exp->growth) = `p2_dL1'"
display "        Indirect (lagged) = `p2_indirect'"
display "Compare to current-period DML: Path1 = -0.029, Path2 = +0.217"
display "=========================================="
