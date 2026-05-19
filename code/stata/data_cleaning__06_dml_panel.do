clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* T07: 构造 DML 面板数据
* 选择 DML 所需变量
keep county_code year D2 D1 gdp_growth_pc fiscal_autonomy ln_fiscal_exp_pc ///
     primary_ratio secondary_ratio ln_pop gov_scale region

* 删除结果变量缺失的行
drop if missing(gdp_growth_pc)

* 删除处理变量缺失的行
drop if missing(D2)

* 对 ln_fiscal_exp_pc 缺失不做删除（T17 单独处理）

* 输出统计信息
di "最终行数: " _N
di "county_code unique: " _N
qui tab county_code
di "unique county_code: " r(r)
di "D2 sum: "
qui sum D2
di r(sum)

* 保存为 CSV
export delimited using "data/processed/dml_panel.csv", replace

di "T07: dml_panel.csv 已保存"
