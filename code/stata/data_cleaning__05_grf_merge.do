clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T05: 构造 GRF 截面结果变量并合并协变量
* 目标：每个县改革后5年均值（year ∈ [reform_pivot, reform_pivot+4]）
* D2=1 使用实际 D2_year；D2=0 使用中位数伪年 2007（T04 已构造）
* 输出：data/processed/grf_input.csv
* ============================================================

* 1. 加载协变量截面数据（包含 reform_pivot，D2=0 已赋值 2007）
preserve
use "data/processed/grf_covariates.dta", clear
tempfile covariates
save `covariates'
restore

* 2. 与面板数据合并以获取 reform_pivot（含 D2=0 的伪年 2007）
merge m:1 county_code using `covariates', keepusing(D2 D1 reform_pivot) keep(3) nogen

* 3. 标记改革后5年窗口（D2=0 使用 reform_pivot=2007 作为对照时间基准）
* 此处不对 D2=0 做特殊处理，让其也参与后5年窗口计算
gen byte post_window = (year >= reform_pivot & year <= reform_pivot + 4) if !missing(reform_pivot)

* 4. 统计每个县在后5年窗口内非空年数
gen byte valid_gdp_growth = (post_window == 1 & gdp_growth_pc != .)
bysort county_code: egen valid_years_gdp = total(valid_gdp_growth)

* 5. 计算后5年 gdp_growth_pc 均值
gen gdp_growth_post = gdp_growth_pc if post_window == 1
bysort county_code: egen gdp_growth_outcome = mean(gdp_growth_post)

* 如果非空观测 < 3 年，置为缺失
replace gdp_growth_outcome = . if valid_years_gdp < 3

* 6. 计算后5年 ln_gdppc 均值（备用结果变量）
gen ln_gdppc_post = ln_gdppc if post_window == 1
bysort county_code: egen ln_gdppc_outcome = mean(ln_gdppc_post)

* 7. 折叠为截面数据（每县一行）
keep county_code gdp_growth_outcome ln_gdppc_outcome
duplicates drop county_code, force

* 8. 合并协变量
merge 1:1 county_code using `covariates', keep(3) nogen

* 9. 检查最终样本
count
tab D2

* 检查结果变量非空率
qui count if gdp_growth_outcome != .
local n_valid = r(N)
qui count
local n_total = r(N)
di "gdp_growth_outcome 全样本非空率：" `n_valid'/`n_total'

qui count if D2 == 1 & gdp_growth_outcome != .
local n_d2_valid = r(N)
qui count if D2 == 1
local n_d2_total = r(N)
di "gdp_growth_outcome D2=1 非空率：" `n_d2_valid'/`n_d2_total'

qui count if D2 == 0 & gdp_growth_outcome != .
local n_d0_valid = r(N)
qui count if D2 == 0
local n_d0_total = r(N)
di "gdp_growth_outcome D2=0 非空率：" `n_d0_valid'/`n_d0_total'

* 10. 列顺序整理并导出 CSV
order county_code D2 D1 reform_pivot gdp_growth_outcome ln_gdppc_outcome ///
      fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ///
      ln_pop_pre gov_scale_pre region_val

* 导出 CSV
export delimited using "data/processed/grf_input.csv", replace

di "T05 完成：已生成 data/processed/grf_input.csv"
di "总样本：`n_total'，D2=1：`n_d2_total'，D2=0：`n_d0_total'"
di "gdp_growth_outcome 非空率 - 全样本：" `n_valid'/`n_total' "，D2=1：" `n_d2_valid'/`n_d2_total' "，D2=0：" `n_d0_valid'/`n_d0_total'
