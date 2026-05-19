"""
Placebo permutation test on D2 ATT using Python.
Approach: keep the same 791 treated counties; shuffle their D2_year values
across counties, breaking county-year matching while preserving timing
distribution. Run TWFE 200 times. Compute placebo p-value.
"""
import pathlib
import numpy as np
import pandas as pd
import pyreadstat
from linearmodels.panel import PanelOLS

ROOT = pathlib.Path(__file__).resolve().parents[3]
DTA = pathlib.Path("data/analysis/panel_analysis_public.dta")
OUT_CSV = ROOT / "outputs" / "tables" / "placebo_year_permutation.csv"
OUT_FIG = ROOT / "outputs" / "figures" / "fig_placebo_distribution.png"

print("Loading panel data...")
df, _ = pyreadstat.read_dta(str(DTA), usecols=[
    "county_code", "year", "gdp_growth_pc", "D2_year",
    "primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"
])
df = df.dropna(subset=["gdp_growth_pc", "primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"]).copy()
print(f"Sample: {len(df)} county-year obs, {df['county_code'].nunique()} counties")

# Construct actual D2 indicator
df["D2"] = ((df["D2_year"].notna()) & (df["year"] >= df["D2_year"])).astype(int)

# Get treated county_codes and their D2_years
treated = df[df["D2_year"].notna()].drop_duplicates("county_code")[["county_code", "D2_year"]]
print(f"Treated counties: {len(treated)}")
treated_codes = treated["county_code"].values
treated_years = treated["D2_year"].values

# Set up panel for linearmodels
df_panel = df.set_index(["county_code", "year"])
controls = ["primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"]
exog_actual = df_panel[["D2"] + controls]
y = df_panel["gdp_growth_pc"]

# Actual TWFE
print("\nRunning actual TWFE...")
model = PanelOLS(y, exog_actual, entity_effects=True, time_effects=True, drop_absorbed=True)
fit = model.fit(cov_type="clustered", cluster_entity=True)
actual_coef = fit.params["D2"]
print(f"Actual D2 ATT: {actual_coef:.4f}")

# Placebo loop
n_perm = 200
np.random.seed(42)
placebo_coefs = []
print(f"\nRunning {n_perm} placebo iterations...")
for i in range(n_perm):
    # Shuffle the D2_year column among treated counties
    shuffled_years = np.random.permutation(treated_years)
    fake_year_map = dict(zip(treated_codes, shuffled_years))

    # Build placebo D2 indicator: same county is fake-treated, but with shuffled year
    df["fake_year"] = df["county_code"].map(fake_year_map)
    df["placebo_D2"] = ((df["fake_year"].notna()) & (df["year"] >= df["fake_year"])).astype(int)

    df_panel_p = df.set_index(["county_code", "year"])
    exog_p = df_panel_p[["placebo_D2"] + controls]

    try:
        model_p = PanelOLS(y, exog_p, entity_effects=True, time_effects=True, drop_absorbed=True)
        fit_p = model_p.fit(cov_type="unadjusted")
        pcoef = fit_p.params["placebo_D2"]
    except Exception:
        pcoef = np.nan
    placebo_coefs.append(pcoef)
    if (i + 1) % 20 == 0:
        print(f"  iter {i+1}/{n_perm}, placebo coef = {pcoef:.4f}")

placebo_coefs = np.array(placebo_coefs)
valid = placebo_coefs[~np.isnan(placebo_coefs)]
print(f"\nValid placebo iterations: {len(valid)}/{n_perm}")
print(f"Placebo coef mean: {valid.mean():.4f}")
print(f"Placebo coef std: {valid.std():.4f}")
print(f"Placebo coef min/max: {valid.min():.3f} / {valid.max():.3f}")
print(f"Placebo coef p5/p95: {np.percentile(valid, 5):.3f} / {np.percentile(valid, 95):.3f}")

# Two-sided placebo p-value
n_extreme = (np.abs(valid) >= abs(actual_coef)).sum()
p_two = n_extreme / len(valid)
n_above = (valid >= actual_coef).sum()
p_one = n_above / len(valid)
print(f"\nPlacebo p (two-sided, |coef| >= |actual|): {p_two:.3f} ({n_extreme}/{len(valid)})")
print(f"Placebo p (one-sided, coef >= actual): {p_one:.3f} ({n_above}/{len(valid)})")

# Save coefs
pd.DataFrame({"iter": range(1, n_perm + 1), "coef": placebo_coefs}).to_csv(OUT_CSV, index=False)
print(f"\nSaved coefficients: {OUT_CSV}")

# Plot
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams["pdf.fonttype"] = 42
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]

fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
ax.hist(valid, bins=30, color="#4A6FA5", edgecolor="white", alpha=0.85)
ax.axvline(actual_coef, color="#C0392B", linewidth=2, linestyle="--",
           label=f"Actual ATT = {actual_coef:.3f}")
ax.axvline(0, color="grey", linewidth=0.8, linestyle=":")
ax.set_xlabel("Placebo D2 coefficient (pp)", fontsize=11)
ax.set_ylabel("Frequency", fontsize=11)
ax.legend(loc="upper left", fontsize=10)
ax.text(0.98, 0.95,
        f"n = {len(valid)} permutations\n"
        f"Placebo mean = {valid.mean():.3f}\n"
        f"Placebo SD = {valid.std():.3f}\n"
        f"p (one-sided) = {p_one:.3f}",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=9, bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.92))
plt.tight_layout()
plt.savefig(OUT_FIG, dpi=300, bbox_inches="tight")
print(f"Saved figure: {OUT_FIG}")
plt.close()
