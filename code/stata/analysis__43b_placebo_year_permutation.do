clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T43B: 主 D2 ATT 安慰剂置换检验（年份置换版）
* 保留相同的 791 个处理县与相同的 D2_year 分布，只随机置换
*  "哪个县获得哪个年份" 的对应关系。
* 这样保留处理强度与时间分布，仅打破 county-year 对应。
* ============================================================

display "=========================================="
display "T43B: Placebo year-permutation test"
display "=========================================="

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* 实际 ATT
reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)
local actual_coef = _b[D2]
display "Actual TWFE D2 ATT: " %6.3f `actual_coef'

* 提取所有处理县的 D2_year 列表
preserve
keep if !missing(D2_year)
duplicates drop county_code, force
keep county_code D2_year
local n_treated = _N
mkmat D2_year, matrix(YEARS)
display "Treated counties: " `n_treated'
restore

set seed 42

* ============================================================
* 200 次置换
* ============================================================
local n_perm = 200
file open fperm using "outputs/tables/placebo_year_permutation.csv", write replace
file write fperm "iter,coef" _n

forval i = 1/`n_perm' {
    quietly {
        preserve

        * 在原始数据上：保留处理县列表，把 D2_year 在县间随机置换
        gen byte _is_treated = !missing(D2_year)

        * 一次性给每个县取一个随机数
        bysort county_code (year): gen byte _first = _n == 1
        gen _rand_perm = .
        replace _rand_perm = uniform() if _first == 1 & _is_treated == 1
        bysort county_code (year): replace _rand_perm = _rand_perm[1]

        * 在 treated 县内按 _rand_perm 排序，分配新的 D2_year
        * 取一个所有 D2_year 的列表
        levelsof D2_year if _is_treated == 1 & _first == 1, local(yrlist)

        * 排序处理县（按随机数）
        gen long _county_id_treated = .
        bysort county_code (year): replace _county_id_treated = _n if _first == 1 & _is_treated == 1
        bysort county_code: replace _county_id_treated = _county_id_treated[1]

        * 简单方法：保留 D2_year 不变，但把 D2_year 在 treated 县间洗牌
        * 实现：把 county_code 替换为随机排序的 county_code
        preserve
            keep if _is_treated == 1 & _first == 1
            keep county_code D2_year
            gen _r = uniform()
            sort _r
            gen _new_order = _n
            keep county_code _new_order
            tempfile mapping
            save `mapping'
        restore
        merge m:1 county_code using `mapping', keep(master match) nogen

        preserve
            keep if _is_treated == 1 & _first == 1
            sort D2_year
            keep D2_year
            gen _new_order = _n
            tempfile yearmap
            save `yearmap'
        restore

        gen _placebo_year = .
        merge m:1 _new_order using `yearmap', keep(master match) nogen update replace

        replace _placebo_year = D2_year if missing(_placebo_year)

        * 重建 placebo_D2 指示变量
        gen byte _placebo_D2 = (year >= _placebo_year) if _is_treated == 1
        replace _placebo_D2 = 0 if missing(_placebo_D2)

        * 跑 TWFE
        capture reghdfe `yvar' _placebo_D2 `controls', absorb(county_code year) cluster(county_code)
        if _rc == 0 {
            local pcoef = _b[_placebo_D2]
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

* ============================================================
* 计算 placebo p 值
* ============================================================
preserve
import delimited "outputs/tables/placebo_year_permutation.csv", clear

quietly count if !missing(coef)
local n_valid = r(N)
quietly count if abs(coef) >= abs(`actual_coef')
local n_extreme = r(N)
local placebo_p = `n_extreme' / `n_valid'

quietly count if coef >= `actual_coef'
local n_above = r(N)
local placebo_p_one = `n_above' / `n_valid'

quietly summarize coef
display "Placebo coef stats: mean=" %6.4f r(mean) ", SD=" %6.4f r(sd) ", min=" %6.3f r(min) ", max=" %6.3f r(max)
display "Placebo p (two-sided, |coef|>=|actual|): " %5.3f `placebo_p' " (" `n_extreme' "/" `n_valid' ")"
display "Placebo p (one-sided, coef>=actual): " %5.3f `placebo_p_one' " (" `n_above' "/" `n_valid' ")"
restore

display "=========================================="
display "T43B SUMMARY"
display "Actual ATT: " %6.3f `actual_coef'
display "Placebo p (two-sided): " %5.3f `placebo_p'
display "Placebo p (one-sided, right tail): " %5.3f `placebo_p_one'
display "=========================================="
