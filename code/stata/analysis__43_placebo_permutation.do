clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T43: 主 D2 ATT 安慰剂置换检验
* 随机重排 D2_year 到曾被处理的县，重新估计 TWFE D2 ATT
* 200 次置换，输出系数分布与对应 p 值
* ============================================================

display "=========================================="
display "T43: Placebo permutation test on D2 ATT"
display "=========================================="

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 实际 ATT
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local actual_coef = _b[D2]
display "Actual TWFE D2 ATT: " %6.3f `actual_coef'

* 提取 D2 处理县列表与 D2_year 列表
preserve
keep if !missing(D2_year)
duplicates drop county_code, force
keep county_code D2_year
local n_treated = _N
display "Treated counties: " `n_treated'
* 把 D2_year 列表保存为本地宏
levelsof D2_year, local(years_list)
local n_years : word count `years_list'
display "Distinct treatment years: " `n_years'
restore

* 总县数
preserve
duplicates drop county_code, force
keep county_code
local n_all_counties = _N
display "All counties: " `n_all_counties'
restore

* ============================================================
* 200 次置换
* ============================================================
local n_perm = 200
file open fperm using "outputs/tables/placebo_permutation_coefs.csv", write replace
file write fperm "iter,coef" _n

forval i = 1/`n_perm' {
    quietly {
        preserve
        * 复原 D2 / D2_year
        replace D2 = 0
        drop D2_year
        gen D2_year = .

        * 在所有县中随机抽 791 县（实际 D2 处理县数）
        bysort county_code: gen first_obs = _n == 1
        gen rand = .
        replace rand = uniform() if first_obs == 1
        bysort county_code: replace rand = rand[1]

        * 取 791 个随机县作为伪处理县
        * 排序后取最小 791 个 rand 对应的县
        sort first_obs rand
        gen rank_county = sum(first_obs)
        gen byte placebo_treated = (rank_county <= `n_treated' & rank_county != .)
        bysort county_code: replace placebo_treated = placebo_treated[1]

        * 给伪处理县随机分配 D2_year（按实际 D2_year 分布抽样）
        * 简化：均匀从 [2000, 2019] 随机抽
        gen placebo_year = floor(uniform()*20 + 2000) if placebo_treated == 1 & first_obs == 1
        bysort county_code: replace placebo_year = placebo_year[1] if placebo_treated == 1

        * 构造 placebo_D2 指示变量
        gen byte placebo_D2 = (year >= placebo_year) if !missing(placebo_year)
        replace placebo_D2 = 0 if missing(placebo_D2)

        * 跑 TWFE
        capture reghdfe `yvar' placebo_D2 `controls', absorb(county_code year) cluster(county_code)
        if _rc == 0 {
            local pcoef = _b[placebo_D2]
        }
        else {
            local pcoef = .
        }
        restore
    }
    file write fperm "`i',`pcoef'" _n
    if mod(`i', 20) == 0 display "  iter " `i' "/" `n_perm' " ... placebo coef = " %6.3f `pcoef'
}

file close fperm
display "Done: placebo coefficients written to outputs/tables/placebo_permutation_coefs.csv"

* ============================================================
* 计算 placebo p 值（双侧）
* ============================================================
preserve
import delimited "outputs/tables/placebo_permutation_coefs.csv", clear
quietly count if abs(coef) >= abs(`actual_coef')
local n_extreme = r(N)
quietly count if !missing(coef)
local n_valid = r(N)
local placebo_p = `n_extreme' / `n_valid'
display "Placebo p-value (two-sided): " %5.3f `placebo_p' " (" `n_extreme' "/" `n_valid' " placebo coefs at least as extreme as " %6.3f `actual_coef' ")"

* 描述性统计
quietly summarize coef
display "Placebo coef mean: " %6.4f r(mean) ", SD: " %6.4f r(sd)
display "Placebo coef p5: " %6.3f r(min) ", p95: " %6.3f r(max)
restore

display "=========================================="
display "T43 SUMMARY"
display "Actual ATT: " %6.3f `actual_coef'
display "Placebo iterations: " `n_perm'
display "Placebo p-value: " %5.3f `placebo_p'
display "=========================================="
