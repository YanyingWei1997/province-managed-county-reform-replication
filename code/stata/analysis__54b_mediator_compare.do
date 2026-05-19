clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T54b: 当期与滞后中介对照（reghdfe 线性版本）
* 与 T36 配套，给出当期 mediator 的 reghdfe 估计作为参照锚
* ============================================================
local controls "primary_ratio secondary_ratio ln_pop gov_scale"
xtset county_code year

display "=========================================="
display "T54b: contemporaneous vs lagged mediator (reghdfe)"
display "=========================================="

* 构造滞后
gen ln_fiscal_exp_pc_L1 = L.ln_fiscal_exp_pc
gen fiscal_autonomy_L1 = L.fiscal_autonomy

* ---- Path 2 contemporaneous ----
display "========== Path 2 contemp: D2 → ln_fiscal_exp_pc (step 1) =========="
reghdfe ln_fiscal_exp_pc D2 `controls', absorb(county_code year) cluster(county_code)
local g_t = _b[D2]
local g_t_se = _se[D2]
display "  γ_t = " %7.4f `g_t' " (SE " %7.4f `g_t_se' ")"

display "========== Path 2 contemp: ln_fiscal_exp_pc → growth | D2 (step 2) =========="
reghdfe gdp_growth_pc D2 ln_fiscal_exp_pc `controls', absorb(county_code year) cluster(county_code)
local d_t = _b[ln_fiscal_exp_pc]
local d_t_se = _se[ln_fiscal_exp_pc]
local d_t_p = 2*(1 - normal(abs(`d_t'/`d_t_se')))
display "  δ_t = " %7.4f `d_t' " (SE " %7.4f `d_t_se' ", p " %5.3f `d_t_p' ")"

local indirect_t = `g_t' * `d_t'
display "  Indirect (contemp) = γ_t × δ_t = " %7.4f `indirect_t'

* ---- Path 1 contemporaneous ----
display "========== Path 1 contemp: D2 → fiscal_autonomy (step 1) =========="
reghdfe fiscal_autonomy D2 `controls', absorb(county_code year) cluster(county_code)
local a_t = _b[D2]
local a_t_se = _se[D2]
display "  α_t = " %7.4f `a_t' " (SE " %7.4f `a_t_se' ")"

display "========== Path 1 contemp: fiscal_autonomy → growth | D2 (step 2) =========="
reghdfe gdp_growth_pc D2 fiscal_autonomy `controls', absorb(county_code year) cluster(county_code)
local b_t = _b[fiscal_autonomy]
local b_t_se = _se[fiscal_autonomy]
local b_t_p = 2*(1 - normal(abs(`b_t'/`b_t_se')))
display "  β_t = " %7.4f `b_t' " (SE " %7.4f `b_t_se' ", p " %5.3f `b_t_p' ")"

local indirect_t1 = `a_t' * `b_t'
display "  Indirect (contemp) = α_t × β_t = " %7.4f `indirect_t1'

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t54b_mediator_compare.csv", write replace
file write fout "spec,gamma_alpha,delta_beta,indirect_pp,note" _n
file write fout "Path2_contemp_reghdfe,`g_t',`d_t',`indirect_t',Step2 mediator at t" _n
file write fout "Path1_contemp_reghdfe,`a_t',`b_t',`indirect_t1',Step2 mediator at t" _n
file close fout

display "=========================================="
display "T54b SUMMARY (reghdfe linear panel mediation)"
display "=========================================="
display "Path 2 contemp: γ × δ = " %7.4f `g_t' " × " %7.4f `d_t' " = " %7.4f `indirect_t' " pp"
display "Path 1 contemp: α × β = " %7.4f `a_t' " × " %7.4f `b_t' " = " %7.4f `indirect_t1' " pp"
display ""
display "Compare with T36 (lagged mediator):"
display "  Path 2 lagged: γ × δ_L1 = 0.0454 × −0.179 = −0.008 pp  ← collapses"
display "  Path 1 lagged: α × β_L1 = −0.0194 × −7.78 = +0.151 pp  ← sign flipped"
display "=========================================="
