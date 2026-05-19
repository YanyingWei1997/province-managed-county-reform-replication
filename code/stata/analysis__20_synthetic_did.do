clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T20: Synthetic DID 稳健性检验
* Arkhangelsky et al. (2021) SDID
* ============================================================

* 安装 sdid（若未安装）
cap which sdid
if _rc != 0 {
    cap ssc install sdid, replace
    if _rc != 0 {
        cap net install sdid, from("https://raw.githubusercontent.com/Daniel-Pailanir/sdid/master/") replace
    }
}

cap which sdid
local sdid_ok = (_rc == 0)
di "sdid 安装状态: `sdid_ok'"

if `sdid_ok' == 1 {
    * ---- 构建强平衡面板 ----
    * 步骤1：保留年份范围 2001-2022
    keep if year >= 2001 & year <= 2022

    * 步骤2：保留 gdp_growth_pc 非缺失
    keep if !missing(gdp_growth_pc)

    * 步骤3：只保留22年完整观测的县（强平衡）
    bysort county_code: gen n_years = _N
    keep if n_years == 22
    drop n_years

    * 步骤4：SDID 要求——剔除首期（2001年）就已处理的县
    bysort county_code (year): gen d2_first = D2[1]
    drop if d2_first == 1
    drop d2_first

    * 确认面板
    xtset county_code year

    * 汇报样本
    di "强平衡面板构建完毕"
    quietly sum county_code if year == 2001
    di "保留县数 = " r(N)
    tab D2 if year == 2001
    di "其中 D2=1 首期处理县已全部剔除"

    * ---- 运行 SDID ----
    di "开始运行 sdid（reps=200, seed=42）..."
    sdid gdp_growth_pc county_code year D2, vce(bootstrap) seed(42) reps(200)

    * 提取结果
    matrix sdid_res = e(b)
    scalar sdid_coef = sdid_res[1,1]

    * 提取 SE
    cap scalar sdid_se = sqrt(e(V)[1,1])
    if _rc != 0 {
        cap scalar sdid_se = e(se)
        if _rc != 0 scalar sdid_se = .
    }

    scalar sdid_ci_l = sdid_coef - 1.96 * sdid_se
    scalar sdid_ci_u = sdid_coef + 1.96 * sdid_se

    * 导出 CSV
    file open fout using "outputs/tables/table_sdid.csv", write replace
    file write fout "method,coef,se,ci_lower,ci_upper" _n
    file write fout "TWFE,1.023,0.339,0.358,1.688" _n
    file write fout "CS-DID,1.192,0.474,0.263,2.122" _n
    file write fout "SDID," (sdid_coef) "," (sdid_se) "," (sdid_ci_l) "," (sdid_ci_u) _n
    file close fout

    di "=== SDID 结果 ==="
    di "SDID coef = " sdid_coef
    di "SDID SE   = " sdid_se
    di "SDID 95%CI = [" sdid_ci_l ", " sdid_ci_u "]"

    if sdid_coef > 0 {
        di "方向检验：PASS — SDID 系数为正，与 TWFE 一致"
    }
    else {
        di "方向检验：WARNING — SDID 系数为负，触发 Major Weakness: SDID_DIRECTION"
    }
}
else {
    * ---- 备用方法：did_imputation ----
    di "sdid 安装失败，尝试 did_imputation"

    cap ssc install did_imputation, replace
    cap which did_imputation
    local didimp_ok = (_rc == 0)

    if `didimp_ok' == 1 {
        keep if year >= 2001 & year <= 2022
        keep if !missing(gdp_growth_pc)
        xtset county_code year

        did_imputation gdp_growth_pc county_code year D2, allhorizons

        matrix res = e(b)
        scalar di_coef = res[1,1]
        scalar di_se   = sqrt(e(V)[1,1])
        scalar di_ci_l = di_coef - 1.96 * di_se
        scalar di_ci_u = di_coef + 1.96 * di_se

        file open fout using "outputs/tables/table_sdid.csv", write replace
        file write fout "method,coef,se,ci_lower,ci_upper" _n
        file write fout "TWFE,1.023,0.339,0.358,1.688" _n
        file write fout "CS-DID,1.192,0.474,0.263,2.122" _n
        file write fout "DID_IMPUTATION," (di_coef) "," (di_se) "," (di_ci_l) "," (di_ci_u) _n
        file close fout

        di "did_imputation 结果已保存（备用方法）"
    }
    else {
        di "ERROR: sdid 和 did_imputation 均安装失败"

        file open fout using "outputs/tables/table_sdid.csv", write replace
        file write fout "method,coef,se,ci_lower,ci_upper" _n
        file write fout "TWFE,1.023,0.339,0.358,1.688" _n
        file write fout "CS-DID,1.192,0.474,0.263,2.122" _n
        file write fout "SDID,NA,NA,NA,NA" _n
        file close fout
    }
}

di "T20 脚本执行完毕"
