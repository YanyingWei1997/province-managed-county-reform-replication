"""
Figure 4: Spatial distribution of CATE and pre-reform fiscal autonomy.

Single-panel design:
  - color: GRF CATE (5-segment diverging, red=more negative, blue=less negative)
  - size: pre-reform fiscal autonomy (larger = higher fa)
  - shape: solid (D2-treated) vs hollow (never-treated)
  - star markers: counties in the paper-threshold highest-CATE PolicyTree leaf
  - province boundaries: from reference folder shapefile

Output: outputs/figures/fig4_spatial_cate.png at 300 DPI
"""
import pathlib

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "stix"

ROOT = pathlib.Path(__file__).resolve().parents[3]
SHP = pathlib.Path(
    "data/external/china_county_shapefile/"
    "2026年04月13日 基于RF与SHAP的地理空间可解释性分析与可视化绘图/2023年省级.shp"
)

# 1. Load data
cate = pd.read_csv(ROOT / "data" / "processed" / "d2_cate_results.csv")
grf = pd.read_csv(ROOT / "data" / "processed" / "grf_input.csv")
geo = pd.read_csv(ROOT / "data" / "processed" / "county_centroids.csv")
top_leaf = pd.read_csv(ROOT / "data" / "processed" / "policytree_paper_threshold_counties.csv")
top_codes = set(top_leaf["county_code"].astype(int))

# Merge CATE + features + coordinates
df = cate.merge(grf, on=["county_code", "D2"], how="inner") \
         .merge(geo[["county_code", "lon", "lat"]], on="county_code", how="inner")
df["cate_pp"] = df["cate"] * 100  # convert to percentage points
df["is_top_leaf"] = df["county_code"].isin(top_codes)
df["is_treated"] = df["D2"].astype(int) == 1
print(f"Final mapping sample: {len(df)} counties")
print(f"  treated (D2=1): {df['is_treated'].sum()}, control (D2=0): {(~df['is_treated']).sum()}")
print(f"  top-leaf (paper threshold): {df['is_top_leaf'].sum()}")
print(f"  CATE range: [{df['cate_pp'].min():.2f}, {df['cate_pp'].max():.2f}] pp")

# 2. Color scheme: 5-segment diverging
boundaries = [-7, -3.5, -2.0, -0.5, 0.5, 2]
colors = ["#67001f", "#d6604d", "#fddbc7", "#92c5de", "#2166ac"]  # red→blue diverging
cmap = ListedColormap(colors)
norm = BoundaryNorm(boundaries, cmap.N)

# 3. Marker size from fiscal_autonomy_pre
fa = df["fiscal_autonomy_pre"].clip(lower=df["fiscal_autonomy_pre"].quantile(0.02),
                                     upper=df["fiscal_autonomy_pre"].quantile(0.98))
size_min, size_max = 8, 60
df["msize"] = size_min + (fa - fa.min()) / (fa.max() - fa.min()) * (size_max - size_min)

# 4. Province boundaries
provs = gpd.read_file(SHP)
print(f"Province shapefile loaded: {len(provs)} features")

# 5. Plot
fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)

# Draw province boundaries (light grey background)
provs.boundary.plot(ax=ax, color="#888888", linewidth=0.4)

# Sort so larger points draw under smaller (so all are visible)
df_sorted = df.sort_values("msize", ascending=True)

# Plot non-top-leaf counties (filled circles, alpha varies by D2 status)
non_top = df_sorted[~df_sorted["is_top_leaf"]]
treated = non_top[non_top["is_treated"]]
control = non_top[~non_top["is_treated"]]

# treated counties: filled circles
sc1 = ax.scatter(treated["lon"], treated["lat"],
                 c=treated["cate_pp"], cmap=cmap, norm=norm,
                 s=treated["msize"], marker="o", edgecolors="white",
                 linewidths=0.3, alpha=0.92, zorder=2)
# control counties: hollow circles (face=light, edge=color)
sc2 = ax.scatter(control["lon"], control["lat"],
                 c=control["cate_pp"], cmap=cmap, norm=norm,
                 s=control["msize"], marker="o", edgecolors="black",
                 linewidths=0.3, alpha=0.55, zorder=1.5)

# Top-leaf counties: gold stars
top = df_sorted[df_sorted["is_top_leaf"]]
ax.scatter(top["lon"], top["lat"], marker="*", s=200,
           facecolors="#FFD700", edgecolors="black", linewidths=0.7,
           zorder=4, label=f"PolicyTree top-leaf (n={len(top)})")

# 6. Decorations
ax.set_xlim(72, 136)
ax.set_ylim(15, 55)
ax.set_xlabel("Longitude (°E)", fontsize=11)
ax.set_ylabel("Latitude (°N)", fontsize=11)
ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.5)
ax.set_aspect(1.15)

# Colorbar (CATE)
cbar = plt.colorbar(sc1, ax=ax, shrink=0.55, pad=0.015,
                    ticks=boundaries, location="right")
cbar.set_label("CATE (pp)", fontsize=10)
cbar.ax.tick_params(labelsize=9)

# Size legend (fiscal autonomy)
fa_quantiles = [df["fiscal_autonomy_pre"].quantile(q) for q in [0.1, 0.5, 0.9]]
fa_sizes = [size_min + (q - fa.min()) / (fa.max() - fa.min()) * (size_max - size_min)
            for q in fa_quantiles]
fa_handles = [
    mlines.Line2D([], [], marker="o", color="w", markerfacecolor="#888",
                  markeredgecolor="#444", markersize=np.sqrt(s),
                  label=f"{q:.2f}")
    for q, s in zip(fa_quantiles, fa_sizes)
]
leg1 = ax.legend(handles=fa_handles, title="fiscal_autonomy_pre",
                 loc="lower left", fontsize=8.5, title_fontsize=9,
                 framealpha=0.92, bbox_to_anchor=(0.01, 0.02))
ax.add_artist(leg1)

# Shape legend (D2 status + top-leaf star)
shape_handles = [
    mlines.Line2D([], [], marker="o", color="w", markerfacecolor="#aaa",
                  markeredgecolor="white", markersize=8, label="D2-treated"),
    mlines.Line2D([], [], marker="o", color="w", markerfacecolor="none",
                  markeredgecolor="black", markersize=8, label="Never-treated"),
    mlines.Line2D([], [], marker="*", color="w", markerfacecolor="#FFD700",
                  markeredgecolor="black", markersize=14,
                  label=f"PolicyTree highest-CATE\nleaf (n={len(top)})"),
]
ax.legend(handles=shape_handles, title="Marker", loc="lower right",
          fontsize=8.5, title_fontsize=9, framealpha=0.92,
          bbox_to_anchor=(0.99, 0.02))

plt.tight_layout()

OUT_PNG = ROOT / "outputs" / "figures" / "fig4_spatial_cate.png"
OUT_PDF = ROOT / "outputs" / "figures" / "fig4_spatial_cate.pdf"
plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.savefig(OUT_PDF, bbox_inches="tight")
print(f"Saved: {OUT_PNG}")
print(f"Saved: {OUT_PDF}")
plt.close()
