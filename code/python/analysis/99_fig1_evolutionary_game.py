"""
Figure 1: The Evolutionary Game of Province-Managed-County Reform.

Three-panel combined figure:
  (a) Replicator-dynamic trajectories: x_P(τ) under different f values
  (b) ESS bifurcation diagram: stable equilibrium x_P* as a function of f
  (c) Empirical-theoretical bridge: KDE of fiscal_autonomy_pre overlaid with f*

Output: paper/figures/fig1_evolutionary_game.png (600 DPI, 14 × 9 inches)
"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Times New Roman font for serif text; fall back gracefully if unavailable.
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams["mathtext.fontset"] = "stix"
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["legend.fontsize"] = 9
plt.rcParams["figure.dpi"] = 100  # display dpi; saved at 600

# ─── Model parameters ────────────────────────────────────────────────
DELTA = 0.3       # prefectural intercept rate
CP_OVER_T = 0.1   # provincial admin cost ratio
Z = 1.0           # productivity scaling
T = 1.0           # transfer normalization
F_STAR = 1.0 - CP_OVER_T / (DELTA * Z * T)   # = 0.6667
print(f"f* = {F_STAR:.4f}")


def delta_pi_P(f):
    """Provincial payoff differential (D2 vs status quo)."""
    return DELTA * Z * T * (1 - f) - CP_OVER_T


def replicator_trajectory(f, x0=0.05, t_max=50.0, n_steps=2000):
    """Simulate replicator dynamics dx/dtau = x(1-x) * delta_pi_P(f)."""
    tau = np.linspace(0, t_max, n_steps)
    dt = tau[1] - tau[0]
    x = np.empty_like(tau)
    x[0] = x0
    dpi = delta_pi_P(f)
    for i in range(1, n_steps):
        # Euler step on replicator equation
        x[i] = x[i - 1] + x[i - 1] * (1 - x[i - 1]) * dpi * dt
        # Clamp to [0, 1] for numerical safety
        x[i] = max(0.0, min(1.0, x[i]))
    return tau, x


# ─── Build figure: 3-panel layout (a top full width; b, c bottom half each) ──
fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0], hspace=0.32, wspace=0.28)
ax_a = fig.add_subplot(gs[0, :])     # top, full width
ax_b = fig.add_subplot(gs[1, 0])     # bottom-left
ax_c = fig.add_subplot(gs[1, 1])     # bottom-right

# ─── Panel (a): Replicator trajectories ──────────────────────────────
f_values = [0.2, 0.4, 0.6, F_STAR, 0.8]
trajectory_colors = {
    0.2: "#B22222",   # firebrick
    0.4: "#CD5C5C",   # indian red
    0.6: "#E9967A",   # darksalmon
    F_STAR: "#DAA520",  # goldenrod (boundary)
    0.8: "#4682B4",   # steelblue
}
for f in f_values:
    tau, x = replicator_trajectory(f)
    label = f"$f = {f:.3f}$" if abs(f - F_STAR) < 1e-3 else f"$f = {f:.1f}$"
    if abs(f - F_STAR) < 1e-3:
        label = f"$f = f^* = {F_STAR:.3f}$ (boundary)"
        ax_a.plot(tau, x, color=trajectory_colors[f], linewidth=2.5,
                  linestyle="--", label=label)
    else:
        ax_a.plot(tau, x, color=trajectory_colors[f], linewidth=2.0,
                  label=label)

# ESS limits as horizontal reference lines
ax_a.axhline(0, color="gray", linewidth=0.5, linestyle=":")
ax_a.axhline(1, color="gray", linewidth=0.5, linestyle=":")
ax_a.text(50.5, 1.0, "$x_P^* = 1$ (full D2 adoption)",
          fontsize=9, color="#555555", va="center")
ax_a.text(50.5, 0.0, "$x_P^* = 0$ (no D2 adoption)",
          fontsize=9, color="#555555", va="center")

# Annotate the divergence
ax_a.annotate(
    "Below $f^*$:\nD2 share $\\to 1$",
    xy=(20, 0.85), xytext=(8, 0.55),
    fontsize=10, color="#8B0000",
    arrowprops=dict(arrowstyle="->", color="#8B0000", lw=1),
)
ax_a.annotate(
    "Above $f^*$:\nD2 share $\\to 0$",
    xy=(20, 0.02), xytext=(8, 0.20),
    fontsize=10, color="#1F4E79",
    arrowprops=dict(arrowstyle="->", color="#1F4E79", lw=1),
)

ax_a.set_xlim(0, 56)
ax_a.set_ylim(-0.05, 1.10)
ax_a.set_xlabel("Evolutionary time $\\tau$")
ax_a.set_ylabel("D2-adopted share $x_P(\\tau)$")
ax_a.set_title("(a) Replicator-dynamic trajectories: strategy share converges to ESS depending on county fiscal autonomy $f$")
ax_a.legend(loc="center right", framealpha=0.9, ncol=1)
ax_a.grid(False)
for spine in ["top", "right"]:
    ax_a.spines[spine].set_visible(False)

# ─── Panel (b): ESS bifurcation diagram ──────────────────────────────
f_grid = np.linspace(0, 1, 1000)

# Shade the two ESS regions
ax_b.axvspan(0, F_STAR, color="#90EE90", alpha=0.25, label="$f < f^*$: D2 is ESS")
ax_b.axvspan(F_STAR, 1, color="#D3D3D3", alpha=0.45, label="$f > f^*$: status quo is ESS")

# Stable branches (solid)
ax_b.plot([0, F_STAR], [1, 1], color="#2E7D32", linewidth=3,
          label="Stable equilibrium ($x_P^* = 1$)")
ax_b.plot([F_STAR, 1], [0, 0], color="#1F4E79", linewidth=3,
          label="Stable equilibrium ($x_P^* = 0$)")

# Unstable branches (dashed)
ax_b.plot([0, F_STAR], [0, 0], color="#1F4E79", linewidth=1.5, linestyle="--",
          alpha=0.7, label="Unstable equilibrium")
ax_b.plot([F_STAR, 1], [1, 1], color="#2E7D32", linewidth=1.5, linestyle="--",
          alpha=0.7)

# Critical threshold
ax_b.axvline(F_STAR, color="#DAA520", linewidth=2, linestyle="-", alpha=0.85)
ax_b.scatter([F_STAR], [F_STAR], color="#DAA520", s=80, zorder=5,
             edgecolors="black", linewidths=1)
ax_b.annotate(
    f"$f^* = {F_STAR:.3f}$",
    xy=(F_STAR, 0.50), xytext=(F_STAR + 0.10, 0.55),
    fontsize=11, color="#8B6914", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#8B6914", lw=1),
)

ax_b.set_xlim(0, 1)
ax_b.set_ylim(-0.10, 1.10)
ax_b.set_xlabel("County fiscal autonomy $f$")
ax_b.set_ylabel("Evolutionarily stable $x_P^*$")
ax_b.set_title("(b) ESS bifurcation: $x_P^*$ flips at $f = f^*$")
ax_b.legend(loc="center right", framealpha=0.9, fontsize=8)
for spine in ["top", "right"]:
    ax_b.spines[spine].set_visible(False)

# ─── Panel (c): Empirical-theoretical bridge ─────────────────────────
# Load fiscal_autonomy from the panel and compute pre-reform mean per county
df = pd.read_stata("data/analysis/panel_analysis_public.dta")

# Pre-reform: years before D2_year for each county; for never-treated, use earliest 3 years
df = df.sort_values(["county_code", "year"]).reset_index(drop=True)

def compute_pre_fa(group):
    """Return mean fiscal_autonomy in 3 years immediately before D2_year (or earliest 3 if never-treated)."""
    d2y = group["D2_year"].iloc[0] if not group["D2_year"].isna().all() else None
    if d2y is None or pd.isna(d2y):
        # Never-treated: use earliest 3 years
        sub = group.head(3)
    else:
        sub = group[(group["year"] >= d2y - 3) & (group["year"] < d2y)]
    fa = sub["fiscal_autonomy"].dropna()
    return fa.mean() if len(fa) > 0 else np.nan

pre_fa = df.groupby("county_code", group_keys=False).apply(compute_pre_fa, include_groups=False).dropna()
print(f"Pre-reform fiscal autonomy: N = {len(pre_fa)}, mean = {pre_fa.mean():.3f}")

# Trim to [0, 1] for visualization (winsorize tail at 1.0)
pre_fa_clipped = pre_fa.clip(0, 1.5)

# KDE
kde = gaussian_kde(pre_fa_clipped, bw_method=0.25)
x_grid = np.linspace(0, 1.5, 500)
density = kde(x_grid)

# Plot density
ax_c.fill_between(
    x_grid[x_grid <= F_STAR], 0, density[x_grid <= F_STAR],
    color="#90EE90", alpha=0.55,
    label=f"$f < f^*$: D2 is ESS regime"
)
ax_c.fill_between(
    x_grid[x_grid > F_STAR], 0, density[x_grid > F_STAR],
    color="#D3D3D3", alpha=0.55,
    label=f"$f > f^*$: status quo regime"
)
ax_c.plot(x_grid, density, color="black", linewidth=1.5)

# Vertical lines
mean_fa = pre_fa.mean()
ax_c.axvline(F_STAR, color="#DAA520", linewidth=2, linestyle="-")
ax_c.axvline(mean_fa, color="#B22222", linewidth=1.8, linestyle="--")

# Mark PolicyTree leaf threshold
LEAF_THRESHOLD = 0.049
ax_c.scatter([LEAF_THRESHOLD], [0], color="black", marker="^", s=70, zorder=5,
             clip_on=False)

# Compute share of counties below f*
share_below = (pre_fa < F_STAR).mean() * 100

# Annotations
ymax = density.max()
ax_c.annotate(
    f"$f^* = {F_STAR:.3f}$\n(theory)",
    xy=(F_STAR, ymax * 0.88), xytext=(F_STAR + 0.13, ymax * 0.95),
    fontsize=9, color="#8B6914", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#8B6914", lw=0.8),
)
ax_c.annotate(
    f"Sample mean\n$\\bar f = {mean_fa:.3f}$",
    xy=(mean_fa, ymax * 0.45), xytext=(mean_fa - 0.30, ymax * 0.65),
    fontsize=9, color="#8B0000",
    arrowprops=dict(arrowstyle="->", color="#8B0000", lw=0.8),
)
ax_c.annotate(
    f"PolicyTree\nleaf cut $0.049$",
    xy=(LEAF_THRESHOLD, 0), xytext=(LEAF_THRESHOLD + 0.10, ymax * 0.18),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=0.8),
)
ax_c.text(
    0.02, ymax * 1.05,
    f"{share_below:.1f}% of counties in ESS-D2 regime",
    fontsize=10, color="#1B5E20", fontweight="bold",
)

ax_c.set_xlim(0, 1.5)
ax_c.set_ylim(0, ymax * 1.15)
ax_c.set_xlabel("Pre-reform fiscal autonomy $f$")
ax_c.set_ylabel("Empirical density")
ax_c.set_title("(c) Empirical $f$ distribution against the ESS threshold")
ax_c.legend(loc="upper right", framealpha=0.9, fontsize=8)
for spine in ["top", "right"]:
    ax_c.spines[spine].set_visible(False)

# ─── Layout & save ───────────────────────────────────────────────────
fig.suptitle(
    "Figure 1. The Evolutionary Game of Province-Managed-County Reform",
    fontsize=14, fontweight="bold", y=1.0
)
plt.tight_layout(rect=[0, 0, 1, 0.97])

out_path = Path("paper/figures/fig1_evolutionary_game.png")
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, dpi=600, bbox_inches="tight")
print(f"Saved -> {out_path}")
print(f"  share below f*: {share_below:.1f}%")
print(f"  N counties (panel c): {len(pre_fa)}")
