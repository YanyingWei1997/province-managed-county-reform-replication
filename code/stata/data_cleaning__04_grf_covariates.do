clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* T04: 构造 GRF 改革前协变量截面数据
* D2_year 中位数 = 2007（来自 T03 数据核查）
* 注意：D2 在面板中是时变变量（改革前=0，改革后=1）
* 需用 max(D2) 构造县级处理指示变量

* -------------------------------------------------------
* 步骤1：构造县级处理指示变量（county_D2, county_D1）
* D2 在面板中为时变变量：改革前0，改革后1
* max(D2)=1 表示该县曾接受过 D2 改革
* -------------------------------------------------------

bysort county_code: egen county_D2 = max(D2)
bysort county_code: egen county_D1 = max(D1)

* -------------------------------------------------------
* 步骤2：确定每县的 reform_pivot
* county_D2=1：reform_pivot = D2_year（县特定，所有行相同）
* county_D2=0：reform_pivot = 2007（全样本 D2_year 中位数）
* -------------------------------------------------------

gen reform_pivot = .
replace reform_pivot = D2_year if county_D2 == 1 & !missing(D2_year)
replace reform_pivot = 2007    if county_D2 == 0

* 验证 reform_pivot 无缺失
count if missing(reform_pivot)
if r(N) > 0 {
    di as error "WARNING: reform_pivot 有 " r(N) " 个缺失值，尝试用 D2_year 填补"
    * 若 D2_year 存在但 reform_pivot 缺失，直接用 D2_year
    replace reform_pivot = D2_year if missing(reform_pivot) & !missing(D2_year)
    replace reform_pivot = 2007    if missing(reform_pivot)
}

* -------------------------------------------------------
* 步骤3：标记改革前3年窗口 year ∈ [reform_pivot-3, reform_pivot-1]
* -------------------------------------------------------

gen pre_window = (year >= reform_pivot - 3) & (year <= reform_pivot - 1)

* -------------------------------------------------------
* 步骤4：计算改革前3年均值
* -------------------------------------------------------

foreach var in fiscal_autonomy primary_ratio secondary_ratio ln_pop gov_scale {
    gen `var'_pre_tmp = `var' if pre_window == 1
    bysort county_code: egen `var'_pre = mean(`var'_pre_tmp)
    drop `var'_pre_tmp
}

* -------------------------------------------------------
* 步骤5：region_val = 数值型地区编码（1=东部，2=中部，3=西部）
* region 为字符串变量，用 region_east/central/west 虚拟变量构造
* -------------------------------------------------------

gen region_num = 1 if region_east == 1
replace region_num = 2 if region_central == 1
replace region_num = 3 if region_west == 1

* 取 reform_pivot 年的 region_num
gen region_at_pivot = region_num if year == reform_pivot
bysort county_code: egen region_val = max(region_at_pivot)

* 若 reform_pivot 年无值，取改革前最近年份（region 通常不随时间变化）
gen region_pre_tmp = region_num if year < reform_pivot
bysort county_code: egen region_pre_max = max(region_pre_tmp)
replace region_val = region_pre_max if missing(region_val)

* 若仍缺失，取全时期最大值（region 不变）
bysort county_code: egen region_any = max(region_num)
replace region_val = region_any if missing(region_val)

drop region_at_pivot region_pre_tmp region_pre_max region_any region_num

* -------------------------------------------------------
* 步骤6：每县保留一行，保留所需变量
* -------------------------------------------------------

bysort county_code: keep if _n == 1

* 重命名县级处理指示变量
rename county_D2 D2_county
rename county_D1 D1_county

keep county_code D2_county D1_county reform_pivot ///
     fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ///
     ln_pop_pre gov_scale_pre region_val

* 重命名为最终变量名
rename D2_county D2
rename D1_county D1

* -------------------------------------------------------
* 步骤7：描述性统计
* -------------------------------------------------------

count
di "总县数: " r(N)

sum reform_pivot, detail
di "reform_pivot 分布：min=" r(min) ", median=" r(p50) ", max=" r(max)

sum fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ///
    ln_pop_pre gov_scale_pre region_val

di "--- D2=1 组（" "） ---"
sum fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ///
    ln_pop_pre gov_scale_pre if D2 == 1

di "--- D2=0 组 ---"
sum fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ///
    ln_pop_pre gov_scale_pre if D2 == 0

* 非空率
foreach var in fiscal_autonomy_pre primary_ratio_pre secondary_ratio_pre ln_pop_pre gov_scale_pre region_val {
    count if !missing(`var')
    di "`var' 非空率: " r(N) "/1537 = " r(N)/1537*100 "%"
}

* -------------------------------------------------------
* 步骤8：保存
* -------------------------------------------------------

save "data/processed/grf_covariates.dta", replace

di "T04 完成：grf_covariates.dta 已保存，总县数=" _N
