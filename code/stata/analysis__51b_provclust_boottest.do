clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T51b: Wild-cluster bootstrap (areg-compatible, one FE absorbed)
* 用 areg 吸收县固定效应，年份用 i.year 显式，使 boottest 兼容
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

encode province, gen(prov_id)
xtset county_code year

display "=========================================="
display "T51b: areg + boottest (province bootcluster)"
display "=========================================="

* 县 FE 由 areg 吸收，年份与省份用显式虚拟
display "========== areg, county FE absorbed, year dummies, cluster province =========="
areg `yvar' D2 D1 `controls' i.year, absorb(county_code) vce(cluster prov_id)
local b = _b[D2]
local s = _se[D2]
local p_asy = 2*(1 - normal(abs(`b'/`s')))
display "  D2 = " %6.4f `b' "  SE_prov = " %6.4f `s' "  p_asym = " %5.3f `p_asy'

display "========== Wild-cluster bootstrap, prov_id =========="
boottest D2, reps(999) cluster(prov_id) bootcluster(prov_id) seed(42) nograph
local p_wild = r(p)
matrix CI = r(CI)
local ci_lo = CI[1,1]
local ci_hi = CI[1,2]
display "  Wild-cluster bootstrap p = " %5.3f `p_wild'
display "  95% CI = [" %6.3f `ci_lo' ", " %6.3f `ci_hi' "]"

* Webb 6-point weights as additional check
display "========== Wild-cluster bootstrap, Webb weights =========="
boottest D2, reps(999) cluster(prov_id) bootcluster(prov_id) weighttype(webb) seed(42) nograph
local p_webb = r(p)
matrix CIw = r(CI)
local ci_w_lo = CIw[1,1]
local ci_w_hi = CIw[1,2]
display "  Webb wild-cluster p = " %5.3f `p_webb'
display "  95% CI = [" %6.3f `ci_w_lo' ", " %6.3f `ci_w_hi' "]"

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t51_provclust.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,ci_lo,ci_hi,note" _n
file write fout "1_county_cluster,0.9980,0.3378,0.003,0.336,1.660,reghdfe county clustering (Table 1 headline)" _n
file write fout "2_province_cluster,0.9980,0.7635,0.191,-0.498,2.494,reghdfe province clustering (asymptotic)" _n
file write fout "3_twoway_county_year,0.9980,0.4999,0.046,0.018,1.978,reghdfe two-way (county+year)" _n
file write fout "4_wild_rad_boottest,`b',,`p_wild',`ci_lo',`ci_hi',areg + boottest 999 reps Rademacher" _n
file write fout "5_wild_webb_boottest,`b',,`p_webb',`ci_w_lo',`ci_w_hi',areg + boottest 999 reps Webb 6pt" _n
file close fout

display "=========================================="
display "T51 / T51b SUMMARY"
display "  Headline (county SE):  D2 = 0.998 (SE 0.338, p 0.003) ***"
display "  Province cluster SE:   D2 = 0.998 (SE 0.764, p 0.191) NS asym"
display "  Two-way (cty+year):    D2 = 0.998 (SE 0.500, p 0.046) **"
display "  Wild-CB Rademacher:    D2 = " %6.4f `b' "  p = " %5.3f `p_wild' ", CI = [" %5.2f `ci_lo' ", " %5.2f `ci_hi' "]"
display "  Wild-CB Webb 6pt:      D2 = " %6.4f `b' "  p = " %5.3f `p_webb' ", CI = [" %5.2f `ci_w_lo' ", " %5.2f `ci_w_hi' "]"
display "=========================================="
