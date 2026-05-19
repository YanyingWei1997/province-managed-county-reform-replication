clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T42: 主因变量缺失数据分析
* 检验 gdp_growth_pc 缺失是否系统地与 D2 / region / year 相关
* ============================================================

display "=========================================="
display "T42: Missing data analysis on gdp_growth_pc"
display "=========================================="

* 总缺失率
quietly count
local n_total = r(N)
quietly count if missing(gdp_growth_pc)
local n_missing = r(N)
local pct_missing = `n_missing' / `n_total' * 100
display "Total observations: " `n_total'
display "Missing gdp_growth_pc: " `n_missing' " (" %5.2f `pct_missing' "%)"

* 缺失指示变量
gen byte missing_y = missing(gdp_growth_pc)
label variable missing_y "Indicator: gdp_growth_pc missing"

* ============================================================
* 1. 按 D2 状态分组的缺失率
* ============================================================
display "========== 1. Missing rate by D2 status =========="
preserve
collapse (mean) missing_y, by(D2)
list, clean
restore

* ============================================================
* 2. 按地区分组的缺失率
* ============================================================
display "========== 2. Missing rate by region =========="
* 从 county_code 前两位推导省份代码，再映射到地区
gen prov2 = floor(county_code/10000)
* East: 11,12,13,14,21,22,23,31,32,33,34,35,36,37,44,46
* Central: 41,42,43
* West: 50,51,52,53,54,61,62,63,64,65
gen byte region_derived = .
replace region_derived = 1 if inlist(prov2, 11,12,13,14,21,22,23,31,32,33,34,35,36,37,44,46)
replace region_derived = 2 if inlist(prov2, 41,42,43)
replace region_derived = 3 if inlist(prov2, 50,51,52,53,54,61,62,63,64,65)
label define reglab 1 "East" 2 "Central" 3 "West"
label values region_derived reglab

preserve
collapse (mean) missing_y (count) county_year=county_code, by(region_derived)
list, clean
restore

* ============================================================
* 3. 按时期分组的缺失率
* ============================================================
display "========== 3. Missing rate by year =========="
preserve
collapse (mean) missing_y, by(year)
list year missing_y, clean noobs
restore

* ============================================================
* 4. 缺失指示对 D2 的回归（核心识别检验）
* ============================================================
display "========== 4. Probit: missing_y on D2 =========="

probit missing_y D2 i.year, cluster(county_code)
local b_d2 = _b[D2]
local se_d2 = _se[D2]
local p_d2 = 2*(1 - normal(abs(`b_d2'/`se_d2')))
display "Probit coef on D2: " %7.4f `b_d2' " (SE " %7.4f `se_d2' ", p " %5.3f `p_d2' ")"

* ============================================================
* 5. 缺失对完整协变量集的回归
* ============================================================
display "========== 5. LPM: missing_y on observables =========="

reghdfe missing_y D2 primary_ratio secondary_ratio ln_pop gov_scale, ///
    absorb(county_code year) cluster(county_code)

local lpm_b_d2 = _b[D2]
local lpm_se_d2 = _se[D2]
local lpm_p_d2 = 2*(1 - normal(abs(`lpm_b_d2'/`lpm_se_d2')))
display "LPM coef on D2 (with county+year FE): " %7.4f `lpm_b_d2' " (SE " %7.4f `lpm_se_d2' ", p " %5.3f `lpm_p_d2' ")"

local lpm_n = e(N)

* ============================================================
* 6. 写入汇总
* ============================================================
file open fout using "outputs/tables/table_missing_analysis.csv", write replace
file write fout "test,coef,se,p_value,N,note" _n
file write fout "Overall_missing_pct,`pct_missing',,,`n_total',Overall missing rate (%)" _n
file write fout "Probit_D2,`b_d2',`se_d2',`p_d2',`n_total',Probit missing on D2 + year FE" _n
file write fout "LPM_D2_with_FE,`lpm_b_d2',`lpm_se_d2',`lpm_p_d2',`lpm_n',LPM missing on D2 with county+year FE + controls" _n
file close fout

display "=========================================="
display "T42 SUMMARY"
display "Overall missing rate: " %5.2f `pct_missing' "%"
display "Probit missing-on-D2 coef: " %7.4f `b_d2' ", p " %5.3f `p_d2'
display "LPM missing-on-D2 (with FE) coef: " %7.4f `lpm_b_d2' ", p " %5.3f `lpm_p_d2'
display "=========================================="
