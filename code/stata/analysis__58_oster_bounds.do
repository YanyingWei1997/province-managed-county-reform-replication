clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T58: Oster (2019) 未观测选择边界
* 关切：观测计量经济学的标准稳健性——若未观测混淆变量需要相对于
*   观测控制变量多强的解释力才能把头条 D2 推至零？
* 检验：用 psacalc 计算 δ*。判读：
*   δ* ≥ 1 → 未观测必须至少与观测一样强 → 头条稳健
*   δ* < 1 → 弱于观测的未观测就足以推翻头条 → 不稳健
* Oster 推荐 R_max = 1.3 × R̂² 作为"完整模型 R²"的合理上界
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 安装 psacalc
cap which psacalc
if _rc {
    display "Installing psacalc..."
    cap ssc install psacalc, replace
}

display "=========================================="
display "T58: Oster (2019) bounds on unobserved selection"
display "=========================================="

xtset county_code year

* ----- Spec 1: Baseline (无 D1，无控制变量；仅 D2 + 双向 FE) -----
display "========== Spec 1: D2 only, with FE, no controls (β̃, R̃²) =========="
reghdfe `yvar' D2, absorb(county_code year) cluster(county_code)
local beta_tilde = _b[D2]
local R2_tilde = e(r2)
local R2_within_tilde = e(r2_within)
display "  β̃ = " %7.4f `beta_tilde'
display "  R̃² (overall) = " %7.4f `R2_tilde'
display "  R̃² (within) = " %7.4f `R2_within_tilde'

* ----- Spec 2: Controlled (D2 + D1 + controls + 双向 FE) -----
display "========== Spec 2: Full controlled (β̂, R̂²) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local beta_hat = _b[D2]
local R2_hat = e(r2)
local R2_within_hat = e(r2_within)
display "  β̂ = " %7.4f `beta_hat'
display "  R̂² (overall) = " %7.4f `R2_hat'
display "  R̂² (within) = " %7.4f `R2_within_hat'

* ----- Spec 3: psacalc 在 areg 后调用 -----
display "========== Spec 3: psacalc — δ* for β = 0 =========="
* psacalc 要求 areg / regress；用 areg + i.year 显式
quietly areg `yvar' D2 D1 `controls' i.year, absorb(county_code) cluster(county_code)
local R2_max_default = min(1.3 * `R2_hat', 1.0)
display "  R_max (Oster recommended 1.3 × R̂²) = " %7.4f `R2_max_default'

* psacalc delta: solve for delta given beta_target = 0
cap noi psacalc delta D2, rmax(`R2_max_default')
if _rc == 0 {
    local delta_star = r(delta)
    display "  δ* (使 β = 0 的未观测/观测选择比) = " %7.4f `delta_star'
}
else {
    display "  psacalc failed; rc = " _rc
    local delta_star = .
}

* psacalc beta: solve for beta given delta = 1 (proportional selection)
cap noi psacalc beta D2, rmax(`R2_max_default') delta(1)
if _rc == 0 {
    local beta_at_delta1 = r(beta)
    display "  β at δ = 1 (assume proportional unobs) = " %7.4f `beta_at_delta1'
}
else {
    display "  psacalc beta failed; rc = " _rc
    local beta_at_delta1 = .
}

* ----- Spec 4: 用更保守的 R_max（不让它太接近 1） -----
display "========== Spec 4: psacalc with R_max = R̂² + 0.05 (more conservative) =========="
local R2_max_cons = `R2_hat' + 0.05
cap noi psacalc delta D2, rmax(`R2_max_cons')
if _rc == 0 {
    local delta_star_cons = r(delta)
    display "  δ* (R_max = R̂² + 0.05) = " %7.4f `delta_star_cons'
}
else {
    local delta_star_cons = .
}

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t58_oster_bounds.csv", write replace
file write fout "spec,beta,R2,note" _n
file write fout "1_no_controls,`beta_tilde',`R2_tilde',Spec 1 baseline (β̃ R̃²)" _n
file write fout "2_full_controls,`beta_hat',`R2_hat',Spec 2 controlled (β̂ R̂²)" _n
file write fout "3_R2_max_1.3x,,`R2_max_default',Oster recommended R_max = 1.3 × R̂²" _n
file write fout "4_delta_star,`delta_star',,Spec 3 δ* for β = 0 at Oster R_max" _n
file write fout "5_beta_delta1,`beta_at_delta1',,β at δ = 1 (proportional unobs)" _n
file write fout "6_delta_star_cons,`delta_star_cons',,δ* with R_max = R̂² + 0.05 conservative" _n
file close fout

display "=========================================="
display "T58 SUMMARY"
display "  β̃ (no controls)        = " %7.4f `beta_tilde'
display "  β̂ (full controls)      = " %7.4f `beta_hat'
display "  R̂²                     = " %7.4f `R2_hat'
display "  R_max (Oster 1.3×R̂²)  = " %7.4f `R2_max_default'
display "  δ* for β = 0            = " %7.4f `delta_star'
display "  β if δ = 1              = " %7.4f `beta_at_delta1'
display "  δ* (conservative R_max) = " %7.4f `delta_star_cons'
display ""
display "  解读："
display "    δ* > 1 → 未观测选择需强于观测才能把 β 推至零 → 头条对未观测选择稳健"
display "    δ* < 1 → 头条不稳健"
display "    若 β at δ=1 同号且大量级 → 在'比例选择'假设下头条仍存活"
display "=========================================="
