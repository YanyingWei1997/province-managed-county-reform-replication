clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T55: GDP 测量误差应对——以财政收入为替代被解释变量
* 关切：中国县级 GDP 数据存在政治报告偏差（Wallace 2014, Holz 2014,
*   Nakamura et al. 2016）。财政收入对应实际入库现金流，造假门槛远高于 GDP。
* 检验：把 ln_fiscal_rev_pc 作为替代被解释变量，看 D2 系数是否同向同量级。
*   若同向同量级 → 头条不是 reporting bias 驱动的伪发现。
* ============================================================
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T55: Fiscal-revenue robustness (reporting-bias check)"
display "=========================================="

* 构造人均财政收入对数（已存在 ln_fiscal_rev_pc）
summ ln_fiscal_rev_pc gdp_growth_pc ln_gdppc, detail
display "已有变量验证：ln_fiscal_rev_pc / gdp_growth_pc / ln_gdppc"

* ----- Spec 1: 头条 GDP 增长率（参照） -----
display "========== Spec 1: Headline (gdp_growth_pc) =========="
reghdfe gdp_growth_pc D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1 = _se[D2]
local p1 = 2*(1 - normal(abs(`b1'/`s1')))
display "  D2 (on gdp_growth_pc) = " %7.4f `b1' " (SE " %7.4f `s1' ", p " %5.3f `p1' ")"

* ----- Spec 2: 替代被解释变量 = ln(人均财政收入) -----
display "========== Spec 2: Outcome = ln_fiscal_rev_pc =========="
reghdfe ln_fiscal_rev_pc D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b2 = _b[D2]
local s2 = _se[D2]
local p2 = 2*(1 - normal(abs(`b2'/`s2')))
local n2 = e(N)
display "  D2 (on ln_fiscal_rev_pc) = " %7.4f `b2' " (SE " %7.4f `s2' ", p " %5.3f `p2' ", N " `n2' ")"
display "  解读：D2 处理使人均财政收入提升约 " %4.1f 100*`b2' " %（exp(b)-1 近似）"

* ----- Spec 3: 财政收入增长率（first-difference of ln_fiscal_rev_pc） -----
display "========== Spec 3: Outcome = D.ln_fiscal_rev_pc (growth rate) =========="
xtset county_code year
gen ln_fiscal_rev_pc_g = D.ln_fiscal_rev_pc * 100
* 缩尾以减少极值
quietly summ ln_fiscal_rev_pc_g, detail
local p1lev = r(p1)
local p99lev = r(p99)
replace ln_fiscal_rev_pc_g = `p1lev' if ln_fiscal_rev_pc_g < `p1lev' & !missing(ln_fiscal_rev_pc_g)
replace ln_fiscal_rev_pc_g = `p99lev' if ln_fiscal_rev_pc_g > `p99lev' & !missing(ln_fiscal_rev_pc_g)
reghdfe ln_fiscal_rev_pc_g D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b3 = _b[D2]
local s3 = _se[D2]
local p3 = 2*(1 - normal(abs(`b3'/`s3')))
local n3 = e(N)
display "  D2 (on fiscal-rev growth, pp) = " %7.4f `b3' " (SE " %7.4f `s3' ", p " %5.3f `p3' ", N " `n3' ")"

* ----- Spec 4: 财政收入/GDP 比（同分子同分母同样可能受偏差影响，但相对更稳健）  -----
display "========== Spec 4: Outcome = fiscal_rev/GDP (×100) =========="
gen rev_gdp_ratio = (fiscal_rev / gdp) * 100
quietly summ rev_gdp_ratio, detail
local p1r = r(p1)
local p99r = r(p99)
replace rev_gdp_ratio = `p1r' if rev_gdp_ratio < `p1r' & !missing(rev_gdp_ratio)
replace rev_gdp_ratio = `p99r' if rev_gdp_ratio > `p99r' & !missing(rev_gdp_ratio)
reghdfe rev_gdp_ratio D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b4 = _b[D2]
local s4 = _se[D2]
local p4 = 2*(1 - normal(abs(`b4'/`s4')))
local n4 = e(N)
display "  D2 (on fiscal_rev/GDP %) = " %7.4f `b4' " (SE " %7.4f `s4' ", p " %5.3f `p4' ", N " `n4' ")"

* ----- Spec 5: 替代水平 ln_gdppc（论文已有的 alt outcome） -----
display "========== Spec 5: Outcome = ln_gdppc (level form) =========="
reghdfe ln_gdppc D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b5 = _b[D2]
local s5 = _se[D2]
local p5 = 2*(1 - normal(abs(`b5'/`s5')))
display "  D2 (on ln_gdppc) = " %7.4f `b5' " (SE " %7.4f `s5' ", p " %5.3f `p5' ")"
display "  解读：D2 使人均 GDP 水平提升约 " %4.1f 100*`b5' " %"

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t55_taxrev_robust.csv", write replace
file write fout "spec,outcome,d2_coef,d2_se,d2_p,n_obs,note" _n
file write fout "1_headline,gdp_growth_pc,`b1',`s1',`p1',24781,Headline (Table 1 reference)" _n
file write fout "2_ln_fiscal_rev_pc,ln_fiscal_rev_pc,`b2',`s2',`p2',`n2',Alt outcome: log per-capita fiscal revenue" _n
file write fout "3_fiscal_rev_growth,D.ln_fiscal_rev_pc_pct,`b3',`s3',`p3',`n3',Alt outcome: fiscal-rev growth rate (pp)" _n
file write fout "4_rev_gdp_ratio,fiscal_rev_to_gdp,`b4',`s4',`p4',`n4',Alt outcome: fiscal_rev/GDP ratio (%)" _n
file write fout "5_ln_gdppc,ln_gdppc,`b5',`s5',`p5',24781,Alt outcome: log per-capita GDP (level)" _n
file close fout

display "=========================================="
display "T55 SUMMARY"
display "  GDP growth rate (headline):       D2 = " %7.4f `b1' "  (p " %5.3f `p1' ")"
display "  ln(fiscal rev pc):                 D2 = " %7.4f `b2' "  (p " %5.3f `p2' ")"
display "  Fiscal rev growth (pp):            D2 = " %7.4f `b3' "  (p " %5.3f `p3' ")"
display "  fiscal_rev/GDP ratio (pct):        D2 = " %7.4f `b4' "  (p " %5.3f `p4' ")"
display "  ln(gdppc):                          D2 = " %7.4f `b5' "  (p " %5.3f `p5' ")"
display "=========================================="
