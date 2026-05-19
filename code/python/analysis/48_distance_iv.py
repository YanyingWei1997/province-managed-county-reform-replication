"""
T48: Distance-to-provincial-capital IV for D2 adoption.

Logic. D2 adoption was rolled out province by province on a staggered schedule.
Within a province, the timing of which counties got reformed first plausibly
depended on geography: provincial governments rolled the reform out either to
closer counties first (easier to monitor) or to remote counties first
(stronger fiscal-intercept problems). Either way, distance to the provincial
capital correlates with D2 timing/intensity.

Distance is time-invariant, so we run a *cross-sectional* IV at the county level:
  D2_intensity_i = α + β·log(distance_i) + γ·X_i + region FE + ε
  Y_i           = a + θ·D2_intensity_i  + γ·X_i + region FE + u

where:
  D2_intensity_i = mean(D2_it) over t (≈ fraction of post-2000 years D2=1)
  Y_i            = mean(gdp_growth_pc_it) over t
  X_i            = pre-period (≤ 2002) covariates
  log(distance_i) = haversine distance from county centroid to provincial capital

Caveats. Distance is plausibly correlated with terrain, market access, etc.
We show the reduced form, first stage, and a sensitivity check that adds
log(population) and sector structure to soak up confounders. This is a
supplementary identification check, not the headline.

Outputs:
  outputs/tables/table_t48_distance_iv.csv
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
np.random.seed(42)

# ---------- 1. Build distance variable ----------
cents = pd.read_csv("data/processed/county_centroids.csv")
caps  = pd.read_csv("data/external/provincial_capitals.csv")

cents["prov_code"] = cents["county_code"] // 10000  # first 2 digits
df_dist = cents.merge(caps[["prov_code", "cap_lon", "cap_lat"]],
                      on="prov_code", how="left")
print(f"Centroids: {len(cents)};  with capital coords: "
      f"{df_dist['cap_lon'].notna().sum()}")

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  # km
    p = np.pi / 180.0
    dlon = (lon2 - lon1) * p
    dlat = (lat2 - lat1) * p
    a = (np.sin(dlat/2)**2
         + np.cos(lat1*p) * np.cos(lat2*p) * np.sin(dlon/2)**2)
    return 2 * R * np.arcsin(np.sqrt(a))

df_dist["dist_km"] = haversine(df_dist["lon"], df_dist["lat"],
                               df_dist["cap_lon"], df_dist["cap_lat"])
df_dist["log_dist"] = np.log(df_dist["dist_km"].clip(lower=1.0))
print(f"Distance distribution (km): "
      f"mean={df_dist['dist_km'].mean():.1f}, "
      f"median={df_dist['dist_km'].median():.1f}, "
      f"max={df_dist['dist_km'].max():.1f}")

dist_panel = df_dist[["county_code", "dist_km", "log_dist"]]

# ---------- 2. Build cross-section panel ----------
import pyreadstat
panel, _ = pyreadstat.read_dta(
    "data/analysis/panel_analysis_public.dta")

needed = ["county_code", "year", "D2", "gdp_growth_pc",
          "primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"]
panel = panel[needed].dropna(subset=["county_code", "year", "D2"])

# Pre-period covariates: years <= 2002 mean
pre_mask = panel["year"] <= 2002
pre = (panel[pre_mask]
       .groupby("county_code")
       [["primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"]]
       .mean()
       .reset_index()
       .rename(columns={c: f"{c}_pre"
                        for c in ["primary_ratio", "secondary_ratio",
                                  "ln_pop", "gov_scale"]}))

# Outcome: post-2000 mean growth
post_mask = panel["year"] >= 2003
out = (panel[post_mask]
       .groupby("county_code")["gdp_growth_pc"]
       .mean()
       .reset_index()
       .rename(columns={"gdp_growth_pc": "y"}))

# Treatment: post-2000 D2 share (intensity)
trt = (panel[post_mask]
       .groupby("county_code")["D2"]
       .mean()
       .reset_index()
       .rename(columns={"D2": "d2_share"}))

cs = (out.merge(trt, on="county_code")
         .merge(pre, on="county_code")
         .merge(dist_panel, on="county_code"))

cs["prov_code"] = cs["county_code"] // 10000
# Region indicator (East / Central / West / Northeast) — coarse
east  = {11,12,13,31,32,33,35,37,44,46}
neast = {21,22,23}
west  = {15,45,50,51,52,53,54,61,62,63,64,65}
def region(p):
    if p in east:  return "East"
    if p in neast: return "Northeast"
    if p in west:  return "West"
    return "Central"
cs["region"] = cs["prov_code"].apply(region)

cs = cs.dropna()
print(f"\nCross-section N = {len(cs)} counties")
print(f"  d2_share mean = {cs['d2_share'].mean():.3f}")
print(f"  y mean = {cs['y'].mean():.3f} pp")

# ---------- 3. First stage ----------
controls = ["primary_ratio_pre", "secondary_ratio_pre",
            "ln_pop_pre", "gov_scale_pre"]
region_dum = pd.get_dummies(cs["region"], prefix="reg", drop_first=True).astype(float)
prov_dum   = pd.get_dummies(cs["prov_code"], prefix="prov", drop_first=True).astype(float)

def add_const(X):
    return sm.add_constant(X.astype(float))

# Spec 1: just log_dist + region FE + pre-controls
X1 = pd.concat([cs[["log_dist"] + controls], region_dum], axis=1)
fs1 = sm.OLS(cs["d2_share"], add_const(X1)).fit(
    cov_type="cluster", cov_kwds={"groups": cs["prov_code"]})
print("\n[First stage 1]  log_dist + pre-controls + region FE")
print(f"  coef on log_dist = {fs1.params['log_dist']:.4f} "
      f"(SE {fs1.bse['log_dist']:.4f}, p {fs1.pvalues['log_dist']:.3f})")
print(f"  F-stat (overall) = {fs1.fvalue:.2f}")

# Spec 2: log_dist + province FE + pre-controls (within-province variation)
X2 = pd.concat([cs[["log_dist"] + controls], prov_dum], axis=1)
fs2 = sm.OLS(cs["d2_share"], add_const(X2)).fit(
    cov_type="cluster", cov_kwds={"groups": cs["prov_code"]})
print("\n[First stage 2]  log_dist + pre-controls + province FE")
print(f"  coef on log_dist = {fs2.params['log_dist']:.4f} "
      f"(SE {fs2.bse['log_dist']:.4f}, p {fs2.pvalues['log_dist']:.3f})")
# Partial F on log_dist for weak-IV diagnostic (1 instrument => F = t^2)
t_lg = fs2.params["log_dist"] / fs2.bse["log_dist"]
F_partial = t_lg ** 2
print(f"  partial F on log_dist = {F_partial:.2f}")

# ---------- 4. Reduced form ----------
rf = sm.OLS(cs["y"], add_const(X2)).fit(
    cov_type="cluster", cov_kwds={"groups": cs["prov_code"]})
print(f"\n[Reduced form]  log_dist coef = {rf.params['log_dist']:.4f} "
      f"(SE {rf.bse['log_dist']:.4f}, p {rf.pvalues['log_dist']:.3f})")

# ---------- 5. 2SLS (manual) ----------
# theta_2SLS = beta_RF / beta_FS
beta_rf = rf.params["log_dist"]
beta_fs = fs2.params["log_dist"]
theta_iv = beta_rf / beta_fs if abs(beta_fs) > 1e-8 else np.nan
print(f"\n[2SLS]  theta = beta_RF / beta_FS = "
      f"{beta_rf:.4f} / {beta_fs:.4f} = {theta_iv:.4f}")

# Use linearmodels.IV2SLS for proper SE
try:
    from linearmodels.iv import IV2SLS
    Xexog = pd.concat([cs[controls], prov_dum], axis=1).astype(float)
    iv = IV2SLS(
        dependent=cs["y"].astype(float),
        exog=add_const(Xexog),
        endog=cs[["d2_share"]].astype(float),
        instruments=cs[["log_dist"]].astype(float),
    ).fit(cov_type="clustered", clusters=cs["prov_code"])
    print(iv.summary)
    theta_iv_lm = float(iv.params["d2_share"])
    se_iv_lm    = float(iv.std_errors["d2_share"])
    p_iv_lm     = float(iv.pvalues["d2_share"])
    ci_lo       = float(iv.conf_int().loc["d2_share", "lower"])
    ci_hi       = float(iv.conf_int().loc["d2_share", "upper"])
    f_first     = float(iv.first_stage.diagnostics.loc["d2_share", "f.stat"])
    print(f"\n[linearmodels 2SLS]  theta = {theta_iv_lm:.4f} pp on d2_share=1")
    print(f"   SE {se_iv_lm:.4f}, p {p_iv_lm:.3f}, CI [{ci_lo:.3f}, {ci_hi:.3f}]")
    print(f"   First-stage F = {f_first:.2f}")
except Exception as e:
    print(f"linearmodels failed: {e}")
    theta_iv_lm = se_iv_lm = p_iv_lm = ci_lo = ci_hi = f_first = np.nan

# ---------- 6. OLS for comparison ----------
ols = sm.OLS(cs["y"], add_const(pd.concat([cs[["d2_share"] + controls], prov_dum], axis=1))).fit(
    cov_type="cluster", cov_kwds={"groups": cs["prov_code"]})
theta_ols = ols.params["d2_share"]
se_ols    = ols.bse["d2_share"]
p_ols     = ols.pvalues["d2_share"]
print(f"\n[OLS, same spec]  d2_share coef = {theta_ols:.4f} "
      f"(SE {se_ols:.4f}, p {p_ols:.3f})")

# ---------- 7. Save ----------
out_rows = [
    dict(spec="OLS_cross_section",
         coef=theta_ols, se=se_ols, p=p_ols,
         ci_lo=theta_ols-1.96*se_ols, ci_hi=theta_ols+1.96*se_ols,
         F_first=np.nan, n=len(cs),
         note="cross-section, province FE, pre-controls, cluster by prov"),
    dict(spec="IV_log_dist_to_capital",
         coef=theta_iv_lm, se=se_iv_lm, p=p_iv_lm,
         ci_lo=ci_lo, ci_hi=ci_hi,
         F_first=f_first, n=len(cs),
         note="2SLS, log_dist as IV for d2_share, province FE, cluster by prov"),
    dict(spec="FirstStage",
         coef=fs2.params["log_dist"], se=fs2.bse["log_dist"],
         p=fs2.pvalues["log_dist"],
         ci_lo=fs2.conf_int().loc["log_dist", 0],
         ci_hi=fs2.conf_int().loc["log_dist", 1],
         F_first=F_partial, n=len(cs),
         note="d2_share on log_dist (province FE)"),
    dict(spec="ReducedForm",
         coef=rf.params["log_dist"], se=rf.bse["log_dist"],
         p=rf.pvalues["log_dist"],
         ci_lo=rf.conf_int().loc["log_dist", 0],
         ci_hi=rf.conf_int().loc["log_dist", 1],
         F_first=np.nan, n=len(cs),
         note="y on log_dist (province FE)"),
]
pd.DataFrame(out_rows).to_csv(
    "outputs/tables/table_t48_distance_iv.csv", index=False)
print("\nSaved -> outputs/tables/table_t48_distance_iv.csv")
print(pd.DataFrame(out_rows).to_string(index=False))
