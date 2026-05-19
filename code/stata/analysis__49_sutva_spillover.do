clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T49: SUTVA / 同地级市内空间溢出检验
* 思路：D2 在 A 县实施后，地级市可能把截留压力转移到同地级市内的非 D2 县。
* 检验：在基准 TWFE 上额外控制"同地级市内当年 D2 县占比（不含自己）"。
* 若 D2 系数 essentially unchanged → 空间溢出可忽略。
* 若 D2 系数显著变小 → 控制组被污染，需要在解读中折扣。
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 用 county_code 前 4 位作为地级市标识
gen prefecture = floor(county_code / 100)

display "=========================================="
display "T49: SUTVA / Within-prefecture spillover"
display "=========================================="

* 计算"同地级市当年 D2 县占比（不含自己）"
* spillover_share = (sum(D2) - D2) / (count - 1)
bysort prefecture year: egen pref_d2_count = total(D2)
bysort prefecture year: egen pref_n = count(D2)
gen pref_d2_others = pref_d2_count - D2
gen pref_n_others = pref_n - 1
gen spillover_share = pref_d2_others / pref_n_others if pref_n_others > 0
replace spillover_share = 0 if missing(spillover_share)

summ spillover_share, detail
display "spillover_share 分布完成"

* 同地级市 D2 邻县总数（绝对值，作为另一个 spec）
gen spillover_count = pref_d2_others

* ============================================================
* Spec 1: 基准 TWFE 复现（含 D1 联合控制）
* ============================================================
display "========== Spec 1: Baseline joint TWFE (Table 1 headline) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
local n1 = e(N)
display "  D2 = " %6.4f `b1' " (SE " %6.4f `s1' ", p " %5.3f `p1' ", N=" `n1' ")"

* ============================================================
* Spec 2: + spillover_share（同地级市 D2 占比）
* ============================================================
display "========== Spec 2: + within-prefecture D2 share =========="
reghdfe `yvar' D2 D1 spillover_share `controls', ///
    absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local b2_sp = _b[spillover_share]
local s2_sp = _se[spillover_share]
local p2_sp = 2*(1 - normal(abs(`b2_sp'/`s2_sp')))
display "  D2 = " %6.4f `b2' " (SE " %6.4f `s2' ", p " %5.3f `p2' ")"
display "  spillover_share = " %6.4f `b2_sp' " (SE " %6.4f `s2_sp' ", p " %5.3f `p2_sp' ")"

* ============================================================
* Spec 3: + spillover_count（同地级市 D2 县数，绝对值）
* ============================================================
display "========== Spec 3: + within-prefecture D2 count =========="
reghdfe `yvar' D2 D1 spillover_count `controls', ///
    absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local b3_sp = _b[spillover_count]
local s3_sp = _se[spillover_count]
display "  D2 = " %6.4f `b3' " (SE " %6.4f `s3' ", p " %5.3f `p3' ")"
display "  spillover_count = " %6.4f `b3_sp' " (SE " %6.4f `s3_sp' ")"

* ============================================================
* Spec 4: + D2 × spillover_share 交互
* ============================================================
display "========== Spec 4: D2 × spillover interaction =========="
gen d2_x_spillover = D2 * spillover_share
reghdfe `yvar' D2 D1 spillover_share d2_x_spillover `controls', ///
    absorb(county_code year) cluster(county_code)
local b4 = _b[D2]
local s4 = _se[D2]
local b4_int = _b[d2_x_spillover]
local s4_int = _se[d2_x_spillover]
display "  D2 (main) = " %6.4f `b4' " (SE " %6.4f `s4' ")"
display "  D2 × spillover_share = " %6.4f `b4_int' " (SE " %6.4f `s4_int' ")"

* ============================================================
* Spec 5: 仅在非 D2 县上回归 spillover_share（直接的污染检验）
* 若 spillover_share 在非 D2 县显著影响增长 → 控制组被污染
* ============================================================
display "========== Spec 5: Pollution test on non-D2 counties =========="
preserve
keep if D2 == 0
reghdfe `yvar' D1 spillover_share `controls', ///
    absorb(county_code year) cluster(county_code)
local b5_sp = _b[spillover_share]
local s5_sp = _se[spillover_share]
local p5_sp = 2*(1 - normal(abs(`b5_sp'/`s5_sp')))
local n5 = e(N)
display "  Non-D2 sample, spillover_share coef = " %6.4f `b5_sp' ///
    " (SE " %6.4f `s5_sp' ", p " %5.3f `p5_sp' ", N=" `n5' ")"
restore

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t49_sutva_spillover.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,spillover_coef,spillover_se,note" _n
file write fout "1_baseline_joint,`b1',`s1',`p1',,,Table 1 headline reproduction" _n
file write fout "2_plus_spillover_share,`b2',`s2',`p2',`b2_sp',`s2_sp',+ within-prefecture D2 share" _n
file write fout "3_plus_spillover_count,`b3',`s3',`p3',`b3_sp',`s3_sp',+ within-prefecture D2 count" _n
file write fout "4_d2_x_spillover_interaction,`b4',`s4',,`b4_int',`s4_int',D2 × spillover share interaction" _n
file write fout "5_pollution_test_nonD2,,,,`b5_sp',`s5_sp',spillover_share on non-D2 sub-sample" _n
file close fout

display "=========================================="
display "T49 SUMMARY"
display "Spec 1 (baseline):              D2 = " %6.4f `b1' " (p " %5.3f `p1' ")"
display "Spec 2 (+ spillover share):     D2 = " %6.4f `b2' " (p " %5.3f `p2' ")"
display "Spec 3 (+ spillover count):     D2 = " %6.4f `b3' " (p " %5.3f `p3' ")"
display "Spec 4 (D2 × spillover):        D2 main = " %6.4f `b4' ", interact = " %6.4f `b4_int'
display "Spec 5 (pollution on non-D2):   spillover = " %6.4f `b5_sp' " (p " %5.3f `p5_sp' ")"
display ""
display "Shift in D2 from Spec 1 -> Spec 2: " %6.4f (`b2' - `b1') " pp"
display "=========================================="
