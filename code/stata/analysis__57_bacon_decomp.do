clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T57: Bacon-Goodman 分解
* 关切：交错 DID 中 TWFE 在"早处理 vs 晚处理"比较上的负权重
*   是 Goodman-Bacon (2021) 的核心诊断。CS-DID 1.192 vs TWFE 0.998
*   的 0.17 pp 差距是否由"坏比较"权重驱动？
* 检验：bacondecomp 把 TWFE 系数分解为：
*   - earlier_treated_vs_later_treated  (后被早处理对照，可能负权)
*   - later_treated_vs_earlier_treated  (前被晚处理对照，标准比较)
*   - treated_vs_never_treated          (干净比较，权重应主导)
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* bacondecomp 要求平衡面板 + 单一处理时点
xtset county_code year

* 构造 D2_year 单一处理时点：从未处理设为 .（never-treated）
gen treat_year = D2_year
* bacondecomp: 处理变量必须是吸收型 0/1 + treat_year（处理时点）

* 检查包安装
cap which bacondecomp
if _rc {
    display "Installing bacondecomp..."
    cap ssc install bacondecomp, replace
}

display "=========================================="
display "T57: Goodman-Bacon decomposition"
display "=========================================="

* 把不平衡面板做成平衡子面板
preserve
* 仅保留全期非缺失样本
quietly count if missing(`yvar')
display "  缺失观测：" r(N)
keep if !missing(`yvar') & !missing(D2)
* bysort county_code: drop if _N != _N_max
bysort county_code: gen n_obs = _N
quietly summ n_obs, detail
display "  county-year obs: min=" r(min) " max=" r(max)

* bacondecomp 要求强平衡
* 取 2001-2022 做平衡子面板（与 SDID 同口径）
keep if year >= 2001 & year <= 2022
bysort county_code: gen n_yrs = _N
keep if n_yrs == 22
quietly count
display "  平衡子样本观测数：" r(N)
quietly tab county_code
display "  平衡子样本县数：" r(r)

* ----- bacondecomp 主分解 -----
display "========== Spec 1: bacondecomp on D2 (balanced sub-panel) =========="
cap noi bacondecomp `yvar' D2, ddetail
if _rc == 0 {
    display "  Bacon decomposition succeeded"
    matrix B = e(sumdd)
    matrix list B
}
else {
    display "  bacondecomp failed; rc = " _rc
    display "  fallback: try without controls"
    cap noi bacondecomp `yvar' D2
}
restore

* ----- 简化版：手动计算"未处理控制权重" -----
display "========== Spec 2: Manual diagnostic — share of clean comparisons =========="
* 对每个 (treated cohort, calendar year) 计算多少 obs 是 never-treated
gen ever_d2 = !missing(D2_year)
bysort year: egen n_year = count(D2)
bysort year: egen n_never_year = total(1 - ever_d2)
gen share_never_year = n_never_year / n_year
quietly summ share_never_year if year >= 2003 & year <= 2019
display "  never-treated 比例（year 2003–2019 区间均值）= " %5.3f r(mean)

* 处理时点分布
display "========== D2_year cohort 分布 =========="
preserve
keep county_code D2_year
duplicates drop
tab D2_year, missing
restore

display "=========================================="
display "T57 SUMMARY"
display "  详见 bacondecomp 输出（上方 matrix list B）"
display "  关键判读：treated_vs_never_treated 权重 + later_vs_earlier 权重 应主导"
display "  earlier_vs_later 权重小 → 负权重问题不严重 → TWFE 0.998 可信"
display "=========================================="
