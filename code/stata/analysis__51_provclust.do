clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T51: 省级聚类与 wild-cluster bootstrap
* 关切：D2 由省级政策决定，22 省 SE 应在更高层级聚类。
* ============================================================
local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

display "=========================================="
display "T51: Province-level clustering & boottest"
display "=========================================="

encode province, gen(prov_id)
count if !missing(prov_id)
display "Provinces (encoded):"
tab prov_id, missing

* ----- Spec 1: 县级聚类（基准） -----
display "========== Spec 1: County clustering (baseline) =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b1 = _b[D2]
local s1_cnty = _se[D2]
local p1_cnty = 2*(1 - normal(abs(`b1'/`s1_cnty')))
display "  D2 = " %6.4f `b1' "  SE_county = " %6.4f `s1_cnty' "  p = " %5.3f `p1_cnty'

* ----- Spec 2: 省级聚类 -----
display "========== Spec 2: Province clustering =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(prov_id)
local b2 = _b[D2]
local s2_prov = _se[D2]
local p2_prov = 2*(1 - normal(abs(`b2'/`s2_prov')))
display "  D2 = " %6.4f `b2' "  SE_prov = " %6.4f `s2_prov' "  p = " %5.3f `p2_prov'

* ----- Spec 3: 双向聚类（县 + 年份） -----
display "========== Spec 3: Two-way clustering (county + year) =========="
cap noi reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code year)
if _rc == 0 {
    local b3 = _b[D2]
    local s3_2way = _se[D2]
    display "  D2 = " %6.4f `b3' "  SE_2way = " %6.4f `s3_2way'
}
else {
    local b3 = `b1'
    local s3_2way = .
    display "  Two-way clustering failed; rc = " _rc
}

* ----- Spec 4: Wild-cluster bootstrap (province), boottest -----
display "========== Spec 4: Wild-cluster bootstrap at province (boottest) =========="
cap which boottest
if _rc {
    display "  Installing boottest..."
    cap ssc install boottest, replace
}
quietly reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(prov_id)
cap noi boottest D2, reps(999) cluster(prov_id) bootcluster(prov_id) seed(42) nograph
if _rc == 0 {
    local p_wild = r(p)
    local ci_wild_lo = r(CIl)
    local ci_wild_hi = r(CIu)
    display "  Wild-cluster bootstrap p (D2) = " %5.3f `p_wild'
    display "  Wild-cluster bootstrap 95% CI = [" %6.3f `ci_wild_lo' ", " %6.3f `ci_wild_hi' "]"
}
else {
    local p_wild = .
    local ci_wild_lo = .
    local ci_wild_hi = .
    display "  boottest failed; rc = " _rc
}

* ============================================================
* 输出
* ============================================================
file open fout using "outputs/tables/table_t51_provclust.csv", write replace
file write fout "spec,d2_coef,d2_se,d2_p,note" _n
file write fout "1_county_cluster,`b1',`s1_cnty',`p1_cnty',Baseline (county clustering)" _n
file write fout "2_province_cluster,`b2',`s2_prov',`p2_prov',Province clustering" _n
file write fout "3_twoway_county_year,`b3',`s3_2way',,Two-way (county+year)" _n
file write fout "4_wild_cluster_boot,`b2',,`p_wild',Wild-cluster bootstrap (province) p-value & CI" _n
file write fout "4_wild_ci_lo,,,`ci_wild_lo'," _n
file write fout "4_wild_ci_hi,,,`ci_wild_hi'," _n
file close fout

display "=========================================="
display "T51 SUMMARY"
display "  D2 (county SE):    " %6.4f `b1' "  (SE " %6.4f `s1_cnty' ", p " %5.3f `p1_cnty' ")"
display "  D2 (province SE):  " %6.4f `b2' "  (SE " %6.4f `s2_prov' ", p " %5.3f `p2_prov' ")"
display "  D2 (2way SE):      " %6.4f `b3' "  (SE " %6.4f `s3_2way' ")"
display "  Wild-CB p:                                 " %5.3f `p_wild'
display "  Wild-CB 95% CI:   [" %6.3f `ci_wild_lo' ", " %6.3f `ci_wild_hi' "]"
display "=========================================="
