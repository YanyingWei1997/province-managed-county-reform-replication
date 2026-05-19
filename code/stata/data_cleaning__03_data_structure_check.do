clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T03: Stata 原始数据结构核查
* 目标：确认所有关键变量存在、格式正确，并输出关键统计量
* ============================================================

** 1. 基本数据结构
describe
di "=== 数据基本信息 ==="
di "观测数: " _N

** 2. 关键变量存在性核查
di ""
di "=== 关键变量存在性核查 ==="

di "--- 标识变量 ---"
capture confirm variable county_code
if _rc == 0 {
    di "county_code: 存在"
}
if _rc != 0 {
    di "county_code: 缺失！"
}

capture confirm variable year
if _rc == 0 {
    di "year: 存在"
}
if _rc != 0 {
    di "year: 缺失！"
}

di "--- 处理变量 ---"
capture confirm variable D
if _rc == 0 {
    di "D: 存在"
}
if _rc != 0 {
    di "D: 缺失！"
}

capture confirm variable D1
if _rc == 0 {
    di "D1: 存在"
}
if _rc != 0 {
    di "D1: 缺失！"
}

capture confirm variable D2
if _rc == 0 {
    di "D2: 存在"
}
if _rc != 0 {
    di "D2: 缺失！"
}

capture confirm variable reform_year
if _rc == 0 {
    di "reform_year: 存在"
}
if _rc != 0 {
    di "reform_year: 缺失！"
}

capture confirm variable D1_year
if _rc == 0 {
    di "D1_year: 存在"
}
if _rc != 0 {
    di "D1_year: 缺失！"
}

capture confirm variable D2_year
if _rc == 0 {
    di "D2_year: 存在"
}
if _rc != 0 {
    di "D2_year: 缺失！"
}

di "--- 结果变量 ---"
capture confirm variable gdp_growth_pc
if _rc == 0 {
    di "gdp_growth_pc: 存在"
}
if _rc != 0 {
    di "gdp_growth_pc: 缺失！"
}

capture confirm variable ln_gdppc
if _rc == 0 {
    di "ln_gdppc: 存在"
}
if _rc != 0 {
    di "ln_gdppc: 缺失！"
}

di "--- 中介/协变量 ---"
capture confirm variable fiscal_autonomy
if _rc == 0 {
    di "fiscal_autonomy: 存在"
}
if _rc != 0 {
    di "fiscal_autonomy: 缺失！"
}

capture confirm variable ln_fiscal_exp_pc
if _rc == 0 {
    di "ln_fiscal_exp_pc: 存在"
}
if _rc != 0 {
    di "ln_fiscal_exp_pc: 缺失！"
}

capture confirm variable primary_ratio
if _rc == 0 {
    di "primary_ratio: 存在"
}
if _rc != 0 {
    di "primary_ratio: 缺失！"
}

capture confirm variable secondary_ratio
if _rc == 0 {
    di "secondary_ratio: 存在"
}
if _rc != 0 {
    di "secondary_ratio: 缺失！"
}

capture confirm variable ln_pop
if _rc == 0 {
    di "ln_pop: 存在"
}
if _rc != 0 {
    di "ln_pop: 缺失！"
}

capture confirm variable gov_scale
if _rc == 0 {
    di "gov_scale: 存在"
}
if _rc != 0 {
    di "gov_scale: 缺失！"
}

capture confirm variable region
if _rc == 0 {
    di "region: 存在"
}
if _rc != 0 {
    di "region: 缺失！"
}

** 3. 关键变量摘要统计
di ""
di "=== 关键变量摘要统计 ==="
summarize county_code year D D1 D2 reform_year D1_year D2_year gdp_growth_pc ln_gdppc fiscal_autonomy ln_fiscal_exp_pc primary_ratio secondary_ratio ln_pop gov_scale

** 4. D2_year 详细分布
di ""
di "=== D2_year 分布 ==="
summarize D2_year, detail
tabulate D2_year, missing

** 5. gdp_growth_pc 非空率（全样本）
di ""
di "=== gdp_growth_pc 非空率 ==="
di "全样本总观测: " _N
count if !missing(gdp_growth_pc)
scalar gc_total = r(N)
di "全样本非空: " gc_total
di "全样本非空率: " round(gc_total/_N * 100, 0.01) "%"

** 6. gdp_growth_pc 非空率（D2=1 子样本）
di ""
di "=== D2=1 子样本 gdp_growth_pc 非空率 ==="
count if D2 == 1
scalar n_d2 = r(N)
di "D2=1 观测数: " n_d2
count if D2 == 1 & !missing(gdp_growth_pc)
scalar gc_d2 = r(N)
di "D2=1 非空: " gc_d2
di "D2=1 非空率: " round(gc_d2/n_d2 * 100, 0.01) "%"

** 7. region 变量检查
di ""
di "=== region 变量分布 ==="
tabulate region, missing

** 8. 面板结构确认
di ""
di "=== 面板结构确认 ==="
xtset county_code year
xtdescribe

di ""
di "=== T03 数据核查完成，无 error ==="
