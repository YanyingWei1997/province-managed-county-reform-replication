clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T53: 预期效应（Anticipation）检验
* 关切：t = -4 处 Sun-Abraham 系数 +0.675 pp 是最大预处理系数；
*   2009 财预 78 号是公开文件，名单县可能在 D2_year - 1 至 -4 已开始反应。
* 检验：
*   (A) 加入 D2_pre2 = 1{t = D2_year - 1 或 -2} 的"预期窗口"虚拟变量，
*       看头条 D2 是否被预期窗口分流。
*   (B) 把"D2 from 2 years before D2_year"作为替代处理指标重跑。
*   (C) 把基准事件研究的参考期换为 t = -3 而非 t = -1（远离潜在预期窗口）。
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 构造相对时间
gen rel_t = year - D2_year if !missing(D2_year)

display "=========================================="
display "T53: Anticipation effect tests"
display "=========================================="

* ----- Spec 1: 基准（参考） -----
display "========== Spec 1: Baseline TWFE (Table 1 headline) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
display "  D2 = " %6.4f `b1' " (SE " %6.4f `s1' ", p " %5.3f `p1' ")"

* ----- Spec 2: 加入预期窗口虚拟变量 (t = -2 或 -1) -----
display "========== Spec 2: + anticipation window (t=-2,-1) =========="
gen ant_window = (rel_t == -1 | rel_t == -2)
replace ant_window = 0 if missing(ant_window)
reghdfe `yvar' D2 D1 ant_window `controls', absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local b2_ant = _b[ant_window]
local s2_ant = _se[ant_window]
local p2_ant = 2*(1 - normal(abs(`b2_ant'/`s2_ant')))
display "  D2 = " %6.4f `b2' " (SE " %6.4f `s2' ", p " %5.3f `p2' ")"
display "  Anticipation window coef = " %6.4f `b2_ant' " (SE " %6.4f `s2_ant' ", p " %5.3f `p2_ant' ")"

* ----- Spec 3: 拓展预期窗口 (t = -4 至 -1) -----
display "========== Spec 3: + wider anticipation window (t=-4 to -1) =========="
gen ant_window4 = (rel_t >= -4 & rel_t <= -1)
replace ant_window4 = 0 if missing(ant_window4)
reghdfe `yvar' D2 D1 ant_window4 `controls', absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local b3_ant = _b[ant_window4]
local s3_ant = _se[ant_window4]
local p3_ant = 2*(1 - normal(abs(`b3_ant'/`s3_ant')))
display "  D2 = " %6.4f `b3' " (SE " %6.4f `s3' ", p " %5.3f `p3' ")"
display "  Anticipation t=-4..-1 coef = " %6.4f `b3_ant' " (SE " %6.4f `s3_ant' ", p " %5.3f `p3_ant' ")"

* ----- Spec 4: 把处理指标提前 2 年（D2 改为从 D2_year-2 起 = 1） -----
display "========== Spec 4: Treat D2 as starting 2 years earlier =========="
gen D2_lead2 = (year >= D2_year - 2) & !missing(D2_year)
reghdfe `yvar' D2_lead2 D1 `controls', absorb(county_code year) cluster(county_code)
local b4 = _b[D2_lead2]
local s4 = _se[D2_lead2]
local p4 = 2*(1 - normal(abs(`b4'/`s4')))
display "  D2_lead2 = " %6.4f `b4' " (SE " %6.4f `s4' ", p " %5.3f `p4' ")"
display "  注：若 D2_lead2 显著，可能是真效应也可能是预期；二者无法分开"

* ----- Spec 5: 仅识别处理后真正发生在 t >= 1 的部分（drop t = 0） -----
display "========== Spec 5: Identify only post-implementation (drop t = 0) =========="
gen D2_post1 = (rel_t >= 1) & !missing(rel_t)
replace D2_post1 = 0 if missing(D2_post1) | D2 == 0
gen drop_t0 = (rel_t == 0) & !missing(rel_t)
reghdfe `yvar' D2_post1 D1 `controls' if drop_t0 == 0, absorb(county_code year) cluster(county_code)
local b5 = _b[D2_post1]
local s5 = _se[D2_post1]
local p5 = 2*(1 - normal(abs(`b5'/`s5')))
display "  D2_post1 (skip year of reform) = " %6.4f `b5' " (SE " %6.4f `s5' ", p " %5.3f `p5' ")"

* ----- Spec 6: 把 D2_year - 1 作为反事实"安慰剂处理"，看其系数 -----
display "========== Spec 6: Pseudo-treatment one year before actual D2_year =========="
gen D2_pseudo = (year >= D2_year - 1) & !missing(D2_year)
reghdfe `yvar' D2_pseudo D1 `controls', absorb(county_code year) cluster(county_code)
local b6 = _b[D2_pseudo]
local s6 = _se[D2_pseudo]
local p6 = 2*(1 - normal(abs(`b6'/`s6')))
display "  D2_pseudo (1 year early) = " %6.4f `b6' " (SE " %6.4f `s6' ", p " %5.3f `p6' ")"

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t53_anticipation.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,ancillary_coef,ancillary_se,note" _n
file write fout "1_baseline,`b1',`s1',`p1',,,Table 1 headline" _n
file write fout "2_anticipation_t-2_-1,`b2',`s2',`p2',`b2_ant',`s2_ant',+ anticipation window dummy t=-2,-1" _n
file write fout "3_anticipation_t-4_-1,`b3',`s3',`p3',`b3_ant',`s3_ant',+ wider anticipation window t=-4..-1" _n
file write fout "4_lead2_treat,`b4',`s4',`p4',,,treatment redefined as starting 2 years earlier" _n
file write fout "5_drop_t0,`b5',`s5',`p5',,,post-treatment indicator skips reform-year cohort" _n
file write fout "6_pseudo_-1,`b6',`s6',`p6',,,pseudo-treatment 1 year before actual D2_year" _n
file close fout

display "=========================================="
display "T53 SUMMARY"
display "  Spec 1 baseline:                     D2 = " %6.4f `b1' " (p " %5.3f `p1' ")"
display "  Spec 2 + ant_window (t=-2,-1):       D2 = " %6.4f `b2' " (p " %5.3f `p2' ")  ant_coef = " %6.4f `b2_ant' " (p " %5.3f `p2_ant' ")"
display "  Spec 3 + ant_window (t=-4..-1):      D2 = " %6.4f `b3' " (p " %5.3f `p3' ")  ant_coef = " %6.4f `b3_ant' " (p " %5.3f `p3_ant' ")"
display "  Spec 4 lead2 (treat 2y earlier):     D2_lead2 = " %6.4f `b4' " (p " %5.3f `p4' ")"
display "  Spec 5 drop t=0:                     D2_post1 = " %6.4f `b5' " (p " %5.3f `p5' ")"
display "  Spec 6 pseudo at t=-1:               D2_pseudo = " %6.4f `b6' " (p " %5.3f `p6' ")"
display "=========================================="
