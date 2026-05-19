clear all
set more off
cd "."
use "data/analysis/panel_analysis_public.dta", clear

* ============================================================
* T59: Missingness sensitivity checks for gdp_growth_pc
* Purpose:
*   Reviewer concern: gdp_growth_pc is missing for 32.6% of county-years,
*   and D2 predicts missingness. This script checks whether the headline
*   complete-case TWFE survives observation-probability reweighting and a
*   Heckman-style control-function diagnostic.
*
* Interpretation discipline:
*   - IPW is used as the main missingness sensitivity check under conditional
*     observability on measured covariates, year FE, and province FE.
*   - The control-function check has no strong exclusion restriction and is
*     therefore reported only as a diagnostic, not as a formal Heckman model.
* ============================================================

local yvar "gdp_growth_pc"
local controls "primary_ratio secondary_ratio ln_pop gov_scale"

cap which reghdfe
if _rc != 0 ssc install reghdfe
cap which ftools
if _rc != 0 ssc install ftools

encode province, gen(prov_id)
gen byte observed_y = !missing(`yvar')
gen prov2 = floor(county_code/10000)
gen byte region_derived = .
replace region_derived = 1 if inlist(prov2, 11,12,13,14,21,22,23,31,32,33,34,35,36,37,44,46)
replace region_derived = 2 if inlist(prov2, 41,42,43)
replace region_derived = 3 if inlist(prov2, 50,51,52,53,54,61,62,63,64,65)
label define reglab59 1 "East" 2 "Central" 3 "West"
label values region_derived reglab59

display "=========================================="
display "T59: Missingness sensitivity checks"
display "=========================================="

quietly count
local n_total = r(N)
quietly count if observed_y == 1
local n_observed = r(N)
local pct_observed = 100 * `n_observed' / `n_total'
display "Total county-years: `n_total'"
display "Observed gdp_growth_pc: `n_observed' (" %5.2f `pct_observed' "%)"

* ----- 1. Complete-case baseline -----
display "========== 1. Complete-case TWFE baseline =========="
reghdfe `yvar' D2 D1 `controls', absorb(county_code year) cluster(county_code)
local b_cc = _b[D2]
local se_cc = _se[D2]
local p_cc = 2*(1 - normal(abs(`b_cc'/`se_cc')))
local n_cc = e(N)
local ci_cc_lo = `b_cc' - 1.96 * `se_cc'
local ci_cc_hi = `b_cc' + 1.96 * `se_cc'
display "Complete-case D2 = " %7.4f `b_cc' " (SE " %7.4f `se_cc' ", p " %6.4f `p_cc' ")"

* ----- 2. Observation model for IPW -----
* Exclude years with mechanically all-missing growth observations.
* Use region rather than province fixed effects in the selection model. A
* province-by-year-rich probit creates complete prediction because some
* province-year cells are entirely observed or entirely missing. The lower-
* dimensional model is more stable and better suited for IPW diagnostics.
display "========== 2. Observation-probability model =========="
probit observed_y D2 D1 `controls' i.year i.region_derived ///
    if inrange(year, 2001, 2022), cluster(county_code)
local n_sel = e(N)
predict double p_obs if e(sample), pr
predict double xb_obs if e(sample), xb
gen byte sel_sample = e(sample)

summ p_obs if e(sample), detail
local p_mean = r(mean)
local p_min = r(min)
local p_p1 = r(p1)
local p_p99 = r(p99)
local p_max = r(max)
display "Predicted Pr(observed): mean=" %6.4f `p_mean' " p1=" %6.4f `p_p1' " p99=" %6.4f `p_p99'

* Stabilized and trimmed inverse-probability weights for observed outcomes.
summ observed_y if e(sample)
local pr_observed = r(mean)
gen double ipw_raw = `pr_observed' / p_obs if observed_y == 1 & sel_sample == 1
gen double ipw_trim = ipw_raw
replace ipw_trim = 10 if ipw_trim > 10 & !missing(ipw_trim)

summ ipw_raw if observed_y == 1 & sel_sample == 1, detail
local w_mean = r(mean)
local w_p99 = r(p99)
local w_max = r(max)
summ ipw_trim if observed_y == 1 & sel_sample == 1, detail
local wt_mean = r(mean)
local wt_p99 = r(p99)
local wt_max = r(max)
display "Raw stabilized IPW: mean=" %6.3f `w_mean' " p99=" %6.3f `w_p99' " max=" %6.3f `w_max'
display "Trimmed IPW:        mean=" %6.3f `wt_mean' " p99=" %6.3f `wt_p99' " max=" %6.3f `wt_max'

* ----- 3. IPW TWFE -----
display "========== 3. IPW complete-case TWFE =========="
reghdfe `yvar' D2 D1 `controls' [pw=ipw_trim] ///
    if observed_y == 1 & !missing(ipw_trim), absorb(county_code year) cluster(county_code)
local b_ipw = _b[D2]
local se_ipw = _se[D2]
local p_ipw = 2*(1 - normal(abs(`b_ipw'/`se_ipw')))
local n_ipw = e(N)
local ci_ipw_lo = `b_ipw' - 1.96 * `se_ipw'
local ci_ipw_hi = `b_ipw' + 1.96 * `se_ipw'
display "IPW D2 = " %7.4f `b_ipw' " (SE " %7.4f `se_ipw' ", p " %6.4f `p_ipw' ")"

* ----- 4. Heckman-style control-function diagnostic -----
* This is not a full Heckman identification design because there is no excluded
* instrument; report as a diagnostic only.
display "========== 4. Control-function diagnostic =========="
gen double imr_obs = normalden(xb_obs) / normal(xb_obs) if observed_y == 1 & sel_sample == 1
reghdfe `yvar' D2 D1 `controls' imr_obs ///
    if observed_y == 1 & !missing(imr_obs), absorb(county_code year) cluster(county_code)
local b_cf = _b[D2]
local se_cf = _se[D2]
local p_cf = 2*(1 - normal(abs(`b_cf'/`se_cf')))
local b_imr = _b[imr_obs]
local se_imr = _se[imr_obs]
local p_imr = 2*(1 - normal(abs(`b_imr'/`se_imr')))
local n_cf = e(N)
local ci_cf_lo = `b_cf' - 1.96 * `se_cf'
local ci_cf_hi = `b_cf' + 1.96 * `se_cf'
display "Control-function D2 = " %7.4f `b_cf' " (SE " %7.4f `se_cf' ", p " %6.4f `p_cf' ")"
display "IMR/control-function term = " %7.4f `b_imr' " (SE " %7.4f `se_imr' ", p " %6.4f `p_imr' ")"

* ----- 5. Simple decision flags -----
local ipw_ratio = `b_ipw' / `b_cc'
local cf_ratio = `b_cf' / `b_cc'
local ipw_flag "PASS"
if (`b_ipw' <= 0 | abs(`ipw_ratio') > 2) local ipw_flag "CAUTION"
if (`wt_max' >= 10) local ipw_flag "`ipw_flag'_WEIGHT_TRIM"
local cf_flag "DIAGNOSTIC_ONLY"
if (`b_cf' <= 0 | abs(`cf_ratio') > 2) local cf_flag "DIAGNOSTIC_CAUTION"

display "========== 5. Interpretation flags =========="
display "IPW coefficient / complete-case coefficient = " %6.3f `ipw_ratio' " -> `ipw_flag'"
display "CF coefficient / complete-case coefficient  = " %6.3f `cf_ratio' " -> `cf_flag'"

* ----- 6. Export summary table -----
cap mkdir outputs/tables
file open fout using "outputs/tables/table_t59_missingness_sensitivity.csv", write replace
file write fout "check,estimate,se,p_value,ci_lo,ci_hi,N,note" _n
file write fout "Complete-case TWFE,`b_cc',`se_cc',`p_cc',`ci_cc_lo',`ci_cc_hi',`n_cc',Baseline county and year FE" _n
file write fout "IPW TWFE,`b_ipw',`se_ipw',`p_ipw',`ci_ipw_lo',`ci_ipw_hi',`n_ipw',Stabilized observation-probability weights trimmed at 10; flag=`ipw_flag'" _n
file write fout "Control-function diagnostic,`b_cf',`se_cf',`p_cf',`ci_cf_lo',`ci_cf_hi',`n_cf',Includes inverse Mills ratio from observation probit; no exclusion restriction; flag=`cf_flag'" _n
file write fout "Observation model mean Pr(obs),`p_mean',,,,,`n_sel',Mean predicted observation probability" _n
file write fout "Observation model p1 Pr(obs),`p_p1',,,,,`n_sel',1st percentile predicted observation probability" _n
file write fout "Observation model p99 Pr(obs),`p_p99',,,,,`n_sel',99th percentile predicted observation probability" _n
file write fout "Trimmed IPW mean,`wt_mean',,,,,`n_ipw',Mean stabilized trimmed weight among observed observations" _n
file write fout "Trimmed IPW p99,`wt_p99',,,,,`n_ipw',99th percentile stabilized trimmed weight" _n
file write fout "Trimmed IPW max,`wt_max',,,,,`n_ipw',Maximum stabilized trimmed weight" _n
file close fout

display "Saved: outputs/tables/table_t59_missingness_sensitivity.csv"
display "=========================================="
display "T59 SUMMARY"
display "  Complete-case: D2 = " %6.3f `b_cc' " (SE " %6.3f `se_cc' ")"
display "  IPW:           D2 = " %6.3f `b_ipw' " (SE " %6.3f `se_ipw' "), flag `ipw_flag'"
display "  Control func.: D2 = " %6.3f `b_cf' " (SE " %6.3f `se_cf' "), flag `cf_flag'"
display "=========================================="
