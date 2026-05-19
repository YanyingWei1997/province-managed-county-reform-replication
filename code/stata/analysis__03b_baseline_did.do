clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T03B: CS-DID / TWFE 基准回归与平行趋势检验
* ============================================================

* 安装必要包
cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools
cap which csdid
if _rc != 0 {
    ssc install csdid
    ssc install drdid
}
cap which estout
if _rc != 0 ssc install estout

* ============================================================
* 0. 数据准备
* ============================================================

* 检查 gdp_growth_pc 缺失率
quietly count if missing(gdp_growth_pc)
local nmiss = r(N)
quietly count
local ntotal = r(N)
local miss_rate = `nmiss' / `ntotal'
display "gdp_growth_pc missing rate: " `miss_rate'

* 若 gdp_growth_pc 缺失率>40%，改用 ln_gdppc
if `miss_rate' > 0.4 {
    display "WARNING: gdp_growth_pc missing rate > 40%, switching to ln_gdppc"
    local yvar "ln_gdppc"
    local yvar_note "被解释变量：ln_gdppc（gdp_growth_pc缺失率>40%）"
}
else {
    local yvar "gdp_growth_pc"
    local yvar_note "被解释变量：gdp_growth_pc"
}

display "Using outcome variable: `yvar'"

* 若 gdp_growth_pc 非空率 = 67.4%，missing = 32.6% < 40%，使用 gdp_growth_pc
* 但按验收标准要求，这里 miss_rate = 0.326 < 0.4，所以用 gdp_growth_pc

* 控制变量
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

* ============================================================
* 1. TWFE 基准回归
* ============================================================
display "========== TWFE 基准回归 =========="

reghdfe `yvar' D2 `controls', absorb(county_code year) cluster(county_code)

* 提取系数和 SE
local twfe_coef = _b[D2]
local twfe_se   = _se[D2]
local twfe_t    = `twfe_coef' / `twfe_se'
local twfe_p    = 2 * (1 - normal(abs(`twfe_t')))
local twfe_ci_lo = `twfe_coef' - 1.96 * `twfe_se'
local twfe_ci_hi = `twfe_coef' + 1.96 * `twfe_se'
local twfe_n    = e(N)

display "TWFE D2 coef = " `twfe_coef'
display "TWFE D2 SE   = " `twfe_se'
display "TWFE D2 p    = " `twfe_p'
display "TWFE CI: [" `twfe_ci_lo' ", " `twfe_ci_hi' "]"
display "N = " `twfe_n'

* ============================================================
* 2. 事件研究（动态效应，平行趋势检验）
* ============================================================
display "========== 事件研究回归 =========="

* 使用已有事件研究虚拟变量，事件期0作为基准期（omit event_0）
* 使用 event_m5 ~ event_m2（前期）和 event_p1 ~ event_p10plus（后期）
* 注意：event_p5plus 不存在，有 event_p5 到 event_p10plus，用 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus 代替

reghdfe `yvar' event_m6plus event_m5 event_m4 event_m3 event_m2 event_m1 ///
    event_p1 event_p2 event_p3 event_p4 event_p5 event_p6 event_p7 event_p8 event_p9 event_p10plus ///
    `controls', absorb(county_code year) cluster(county_code)

* 提取各期系数和 CI，写入 CSV
* 基准期（event_0）系数为 0

local periods "m6plus m5 m4 m3 m2 m1 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10plus"
local period_nums "-6 -5 -4 -3 -2 -1 1 2 3 4 5 6 7 8 9 10"

* 创建 event study CSV
file open fcsv using "data/processed/event_study_coefs.csv", write replace
file write fcsv "period,coef,ci_lower,ci_upper,se" _n

* 写入基准期 0
file write fcsv "0,0,0,0,0" _n

* 写入各期
local i = 1
foreach p of local periods {
    local pnum : word `i' of `period_nums'
    local coef = _b[event_`p']
    local se   = _se[event_`p']
    local cilo = `coef' - 1.96 * `se'
    local cihi = `coef' + 1.96 * `se'
    file write fcsv "`pnum',`coef',`cilo',`cihi',`se'" _n
    local i = `i' + 1
}
file close fcsv

display "事件研究系数已写入 data/processed/event_study_coefs.csv"

* 平行趋势 F 检验（event_m5 ~ event_m2 联合显著性）
test event_m5 event_m4 event_m3 event_m2
local pt_F = r(F)
local pt_p = r(p)
display "平行趋势 F 检验 (event_m5~event_m2): F=" `pt_F' ", p=" `pt_p'

if `pt_p' < 0.1 {
    display "WARNING: 平行趋势检验 p < 0.1，需在报告中标注"
}

* 保存平行趋势结果到本地宏供后续使用
local pt_F_val  = `pt_F'
local pt_p_val  = `pt_p'

* ============================================================
* 3. CS-DID（Callaway-Sant'Anna）
* ============================================================
display "========== CS-DID 回归 =========="

* 准备 D2_year 变量：控制组（D2=0）的 D2_year 设为 0（gvar=0 表示从不处理）
* 注意：D2 是时变指标，D2==0在处理前年份，因此不能用 D2==0 来判断是否为控制县
* 必须按县固定 gvar：使用 D2_year 的县级最大值（D2_year 只在处理后才有值）

* 构造县级 gvar：每个县取其 D2_year 的最大非缺失值
bysort county_code: egen gvar_max = max(D2_year)

* 将 float 转换为 integer
gen int gvar = int(gvar_max)
drop gvar_max

* 从未处理的县（D2_year 始终缺失）：gvar 将为 . (missing)，设为 0
replace gvar = 0 if missing(gvar)

* 将 2000 年前处理的县（always-treated）设为 0（按 CS-DID 惯例排除）
replace gvar = 0 if gvar < 2000

label variable gvar "D2改革年份（0=从不处理，按县固定）"

* 诊断：显示 gvar 分布
tab gvar, missing

* 运行 CS-DID
* 需要保留非缺失观测，因为 csdid 要求配对平衡观测
preserve
keep if !missing(`yvar') & !missing(primary_ratio) & !missing(secondary_ratio) ///
    & !missing(ln_pop) & !missing(gov_scale)

* 先排序
sort county_code year

* 检查保留观测数
quietly count
local csdid_n_obs = r(N)
display "CS-DID 样本量（删除缺失后）: " `csdid_n_obs'

* 尝试 method(drimp) 先，如失败用 method(reg)
cap csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(drimp)
if _rc != 0 | e(N)==0 {
    display "drimp 失败，尝试 method(reg)"
    csdid `yvar' `controls', ivar(county_code) time(year) gvar(gvar) method(reg)
}

* 提取 ATT(simple)
csdid_estat simple

* 提取结果（从矩阵提取）
matrix res = r(table)
* ATT(simple) 是 csdid_estat simple 的第一行
local csdid_coef = res[1,1]
local csdid_se   = res[2,1]
local csdid_ci_lo = res[5,1]
local csdid_ci_hi = res[6,1]

display "CS-DID ATT(simple) = " `csdid_coef'
display "CS-DID SE          = " `csdid_se'
display "CS-DID CI: [" `csdid_ci_lo' ", " `csdid_ci_hi' "]"
restore

* ============================================================
* 4. 汇总输出 table_twfe_csdid.csv
* ============================================================

file open fout using "outputs/tables/table_twfe_csdid.csv", write replace
file write fout "method,coef,se,ci_lower,ci_upper,p,N,outcome_var" _n
file write fout "TWFE,`twfe_coef',`twfe_se',`twfe_ci_lo',`twfe_ci_hi',`twfe_p',`twfe_n',`yvar'" _n
file write fout "CS-DID,`csdid_coef',`csdid_se',`csdid_ci_lo',`csdid_ci_hi',,.,`yvar'" _n
file close fout

display "结果已写入 outputs/tables/table_twfe_csdid.csv"

* ============================================================
* 5. 平行趋势结果补充写入
* ============================================================
file open fpt using "outputs/tables/parallel_trend_test.csv", write replace
file write fpt "test,F_stat,p_value,note" _n
if `pt_p' < 0.1 {
    file write fpt "pre_trend_joint,`pt_F_val',`pt_p_val',WARNING: p<0.1 平行趋势不满足" _n
}
else {
    file write fpt "pre_trend_joint,`pt_F_val',`pt_p_val',通过" _n
}
file close fpt

display "========== T03B 完成 =========="
display "TWFE coef: `twfe_coef'"
display "CS-DID coef: `csdid_coef'"
display "PT F: `pt_F_val', p: `pt_p_val'"
