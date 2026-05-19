clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* 22_event_study_multi.do
* 四结果变量事件研究：GDP增长率 / ln人均GDP / 财政自主度 / ln人均财政收入
* ============================================================

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools

local controls "primary_ratio secondary_ratio ln_pop gov_scale"
local periods  "m6plus m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local pnums    "-6 -5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"

* 四个结果变量及输出文件
local yvars   "gdp_growth ln_gdppc fiscal_autonomy ln_fiscal_rev_pc"
local outfiles "es_gdp_growth es_ln_gdppc es_fiscal_autonomy es_fiscal_rev_pc"

local k = 1
foreach yvar of local yvars {
    local outfile : word `k' of `outfiles'

    display _n "========== 事件研究：`yvar' =========="

    cap reghdfe `yvar' event_m6plus event_m5 event_m4 event_m3 event_m2 event_m1 ///
        event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 ///
        event_p8 event_p9 event_p10plus ///
        `controls', absorb(county_code year) cluster(county_code)

    if _rc != 0 {
        display "WARNING: `yvar' 回归失败，跳过"
        local k = `k' + 1
        continue
    }

    * 写 CSV
    file open fcsv using "data/processed/`outfile'.csv", write replace
    file write fcsv "period,coef,ci_lower,ci_upper,se" _n
    file write fcsv "0,0,0,0,0" _n

    local i = 1
    foreach p of local periods {
        local pnum : word `i' of `pnums'
        local coef = _b[event_`p']
        local se   = _se[event_`p']
        local cilo = `coef' - 1.96 * `se'
        local cihi = `coef' + 1.96 * `se'
        file write fcsv "`pnum',`coef',`cilo',`cihi',`se'" _n
        local i = `i' + 1
    }
    file close fcsv

    * 平行趋势 F 检验
    test event_m5 event_m4 event_m3 event_m2
    display "`yvar' 平行趋势 F=" r(F) "  p=" r(p)

    display "已保存：data/processed/`outfile'.csv"
    local k = `k' + 1
}

display _n "========== 22_event_study_multi 完成 =========="
