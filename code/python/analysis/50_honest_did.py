"""
T50: Rambachan-Roth (2023) honest DID sensitivity bands.

The headline TWFE ATT (0.998 pp) is identified under parallel trends. The pre-trend
joint F-test does not reject (F = 1.12, p = 0.345), but the placebo year-permutation
gave p = 0.080, raising a residual concern. R-R formalizes the question: how large
a deviation from parallel trends can the conclusion withstand?

We compute two bound families:
  Δ^SD(M) — smoothness restriction. Post-treatment bias bounded by
      M × max_{s<0} |β_{s+1} − 2β_s + β_{s−1}| (max 2nd-difference of pre-period).
  Δ^RM(M) — relative magnitudes. Bias bounded by
      M × max_{s<0} |β_s| (max pre-period coefficient).

For each family, report the bias-adjusted 95% CI for the post-treatment ATT at
M ∈ {0.25, 0.5, 1.0, 2.0}, plus the *breakdown M* at which the lower CI just
touches zero.

Inputs: Sun-Abraham and Gardner pre-period coefficients (the cohort-corrected
estimators), plus the static TWFE ATT (0.998 pp, SE 0.338).

Outputs: outputs/tables/table_t50_honest_did.csv
"""
import os
import numpy as np
import pandas as pd

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# ---------- 1. Inputs ----------
# Static TWFE headline ATT (joint with D1)
ATT, ATT_SE = 0.998, 0.338
zcrit = 1.96  # 95%

# Pre-period event-study coefficients
sa = pd.read_csv("data/processed/es_sunab.csv")
sa_pre = (sa[(sa.period < 0)]
          .sort_values("period")
          .reset_index(drop=True))
print("Sun-Abraham pre-period:")
print(sa_pre[["period", "coef"]].to_string(index=False))

# Gardner: try es_all_specs.csv or fallback
es_all = None
for fp in ["data/processed/es_all_specs.csv",
           "data/processed/es_did2s.csv"]:
    if os.path.exists(fp):
        es_all = pd.read_csv(fp)
        break

gardner_pre_coefs = None
if es_all is not None:
    print("\nFound:", fp)
    print("cols:", es_all.columns.tolist()[:8])
    # Try to detect Gardner column
    for col in ["gardner", "gardner_coef", "did2s_coef", "coef_gardner"]:
        if col in es_all.columns:
            tmp = es_all[es_all["period"] < 0].sort_values("period")
            gardner_pre_coefs = tmp[col].values
            break

# If Gardner not parsed, fall back to known Gardner pre-period coefs from §4.3
# (paper text reports: "Gardner gives a similar pre-treatment pattern with point
# estimates between -0.4 pp and 0.7 pp"). For sensitivity, use SA as primary.
if gardner_pre_coefs is None:
    gardner_pre_coefs = np.array([])  # treat SA as the only series

# ---------- 2. Helpers ----------
def max_pre_coef(coefs):
    """Δ^RM bound: max |β_s| over pre-period."""
    return float(np.max(np.abs(coefs))) if len(coefs) else np.nan

def max_pre_2diff(coefs):
    """Δ^SD bound: max |β_{s+1} − 2β_s + β_{s−1}| over pre-period."""
    if len(coefs) < 3:
        return np.nan
    second_diffs = coefs[2:] - 2 * coefs[1:-1] + coefs[:-2]
    return float(np.max(np.abs(second_diffs)))

def bound_RM(M, max_pre):
    return M * max_pre

def bound_SD(M, max_2d):
    return M * max_2d

def adjusted_CI(att, se, bias_bound):
    """R-R bias-adjusted 95% CI: [att - z*SE - bias, att + z*SE + bias]."""
    return att - zcrit * se - bias_bound, att + zcrit * se + bias_bound

def breakdown_M(att, se, max_unit):
    """The M at which the lower CI bound exactly hits zero.
       att - z*SE - M*max_unit = 0  ⇒  M = (att - z*SE) / max_unit
    """
    margin = att - zcrit * se
    if margin <= 0 or max_unit <= 0:
        return 0.0
    return margin / max_unit

# ---------- 3. Compute bounds (Sun-Abraham as primary) ----------
sa_coefs = sa_pre["coef"].values
max_pre_sa = max_pre_coef(sa_coefs)
max_2d_sa = max_pre_2diff(sa_coefs)
print(f"\nSun-Abraham:")
print(f"  max |pre-coef|      = {max_pre_sa:.4f} pp")
print(f"  max |2nd-difference|= {max_2d_sa:.4f} pp")

# Static ATT margin
margin = ATT - zcrit * ATT_SE
print(f"\nStatic TWFE ATT = {ATT:.3f} pp (SE {ATT_SE:.3f})")
print(f"  Standard 95% CI = [{ATT - zcrit*ATT_SE:.3f}, {ATT + zcrit*ATT_SE:.3f}]")
print(f"  margin (lower bound above zero) = {margin:.3f} pp")

records = []
for M in [0.25, 0.5, 1.0, 2.0]:
    # Δ^RM
    b_rm = bound_RM(M, max_pre_sa)
    lo_rm, hi_rm = adjusted_CI(ATT, ATT_SE, b_rm)
    # Δ^SD
    b_sd = bound_SD(M, max_2d_sa)
    lo_sd, hi_sd = adjusted_CI(ATT, ATT_SE, b_sd)
    records.append(dict(
        family="Δ^RM (relative magnitudes)", M=M,
        bias_bound_pp=b_rm, ci_lo=lo_rm, ci_hi=hi_rm,
        excludes_zero=lo_rm > 0))
    records.append(dict(
        family="Δ^SD (smoothness, 2nd diff)", M=M,
        bias_bound_pp=b_sd, ci_lo=lo_sd, ci_hi=hi_sd,
        excludes_zero=lo_sd > 0))

# Breakdown M
M_break_RM = breakdown_M(ATT, ATT_SE, max_pre_sa)
M_break_SD = breakdown_M(ATT, ATT_SE, max_2d_sa)
print(f"\nBreakdown M (lower CI = 0):")
print(f"  Δ^RM: M* = {M_break_RM:.3f}  (bias = {M_break_RM*max_pre_sa:.3f} pp)")
print(f"  Δ^SD: M* = {M_break_SD:.3f}  (bias = {M_break_SD*max_2d_sa:.3f} pp)")

out = pd.DataFrame(records)
print("\nSensitivity table:")
print(out.to_string(index=False))

# Append breakdown rows
out_break = pd.DataFrame([
    dict(family="Δ^RM (relative magnitudes)", M=round(M_break_RM, 4),
         bias_bound_pp=round(M_break_RM * max_pre_sa, 4),
         ci_lo=0.0, ci_hi=2 * (ATT + zcrit * ATT_SE),
         excludes_zero=False, note="Breakdown M: lower CI = 0"),
    dict(family="Δ^SD (smoothness)", M=round(M_break_SD, 4),
         bias_bound_pp=round(M_break_SD * max_2d_sa, 4),
         ci_lo=0.0, ci_hi=2 * (ATT + zcrit * ATT_SE),
         excludes_zero=False, note="Breakdown M: lower CI = 0"),
])
final = pd.concat([out, out_break], ignore_index=True)
final["max_pre_coef_pp"] = max_pre_sa
final["max_2nd_diff_pp"] = max_2d_sa
final["att_pp"] = ATT
final["att_se"] = ATT_SE

os.makedirs("outputs/tables", exist_ok=True)
final.to_csv("outputs/tables/table_t50_honest_did.csv", index=False)
print("\nSaved -> outputs/tables/table_t50_honest_did.csv")
