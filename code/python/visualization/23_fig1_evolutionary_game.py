"""
fig1_evolutionary_game  -  Three-panel figure for the evolutionary game.

Panels:
  (a) Replicator-dynamic trajectories x_P(τ) at five f values.
  (b) Provincial payoff differential Δπ_P(f) with sign-coded regions and f*.
  (c) Empirical kernel density of pre-reform fiscal autonomy with f* and mean.

Style: matches outputs/figures/22_final_figures.py (serif 7 pt, FIG_WIDTH=6.85,
clean spines, limited palette, no suptitle, no arrows, no pixelated 'Figure 1'
label baked into the image).
"""
import os
import warnings

import matplotlib
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

warnings.filterwarnings("ignore")
os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.makedirs("outputs/figures", exist_ok=True)

# ══════════════════════════════════════════════════════════════
# Palette: red–blue only (matched to fig2_identification)
#   Below f*  (D2 favored)   →  blue family   (deep / medium / light)
#   Boundary  (f = f*)       →  black dashed
#   Above f*  (status quo)   →  red
#   Region fills             →  very soft red / blue tints
# ══════════════════════════════════════════════════════════════
C_NAVY   = '#1B3F6E'     # deep blue
C_BLUE   = '#2E75B6'     # medium blue
C_LBLUE  = '#9FC5E8'     # light blue
C_RED    = '#C0392B'     # red
C_LRED   = '#E8A89C'     # light red (status-quo region fill, low alpha)
C_LLBLUE = '#D6E8F7'     # very light blue (D2-ESS region fill)
C_GRAY   = '#4A4A4A'
C_MGRAY  = '#909090'
C_LGRAY  = '#CACACA'
C_BLACK  = '#1A1A1A'

FIG_WIDTH = 6.85

matplotlib.rcParams.update({
    'font.family':         'serif',
    'font.serif':          ['Times New Roman', 'Times', 'DejaVu Serif'],
    'mathtext.fontset':    'stix',
    'font.size':            7,
    'axes.labelsize':       7,
    'xtick.labelsize':      6.5,
    'ytick.labelsize':      6.5,
    'legend.fontsize':      6,
    'axes.linewidth':       0.5,
    'axes.edgecolor':       C_GRAY,
    'xtick.major.width':    0.5,
    'ytick.major.width':    0.5,
    'xtick.major.size':     2.5,
    'ytick.major.size':     2.5,
    'xtick.direction':      'in',
    'ytick.direction':      'in',
    'axes.spines.top':      False,
    'axes.spines.right':    False,
    'figure.dpi':           300,
    'pdf.fonttype':         42,
    'ps.fonttype':          42,
    'legend.frameon':       False,
    'legend.handlelength':  1.2,
    'legend.handletextpad': 0.4,
    'legend.borderpad':     0.3,
})


def panel_label(ax, label, x=-0.10, y=1.08, size=8):
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=size, fontweight='normal', va='top', ha='left',
            color=C_BLACK)


# ══════════════════════════════════════════════════════════════
# Model
# ══════════════════════════════════════════════════════════════
DELTA = 0.3        # prefectural intercept rate
CP_T  = 0.1        # provincial admin cost ratio (c_P / T)
Z     = 1.0
T     = 1.0
F_STAR = 1.0 - CP_T / (DELTA * Z * T)


def delta_pi_P(f):
    return DELTA * Z * T * (1 - f) - CP_T


def trajectory(f, x0=0.05, t_max=80.0, n_steps=4000):
    tau = np.linspace(0, t_max, n_steps)
    dt  = tau[1] - tau[0]
    x   = np.empty_like(tau)
    x[0] = x0
    dpi  = delta_pi_P(f)
    for i in range(1, n_steps):
        x[i] = x[i - 1] + x[i - 1] * (1 - x[i - 1]) * dpi * dt
        x[i] = max(0.0, min(1.0, x[i]))
    return tau, x


# ══════════════════════════════════════════════════════════════
# Build figure: top full-width panel (a); bottom row panels (b),(c)
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(FIG_WIDTH, 4.6))
gs  = gridspec.GridSpec(2, 2, figure=fig,
                        height_ratios=[1.05, 1.0],
                        hspace=0.42, wspace=0.32,
                        left=0.08, right=0.97, top=0.95, bottom=0.10)
ax_a = fig.add_subplot(gs[0, :])
ax_b = fig.add_subplot(gs[1, 0])
ax_c = fig.add_subplot(gs[1, 1])

# ── Panel (a): replicator trajectories ────────────────────────
f_values = [0.20, 0.40, 0.60, F_STAR, 0.80]
colors_a = {
    0.20:    C_NAVY,
    0.40:    C_BLUE,
    0.60:    C_LBLUE,
    F_STAR:  C_BLACK,    # boundary in black, dashed
    0.80:    C_RED,
}

for f in f_values:
    tau, x = trajectory(f, t_max=60.0)
    is_boundary = abs(f - F_STAR) < 1e-3
    label = (f"$f = f^* = {F_STAR:.3f}$"
             if is_boundary
             else f"$f = {f:.2f}$")
    ax_a.plot(tau, x,
              color=colors_a[f],
              lw=1.4,
              ls='-' if not is_boundary else '--',
              label=label,
              zorder=4 if is_boundary else 3)

ax_a.axhline(0, color=C_MGRAY, lw=0.4, ls=':', zorder=1)
ax_a.axhline(1, color=C_MGRAY, lw=0.4, ls=':', zorder=1)

ax_a.set_xlim(0, 60)
ax_a.set_ylim(-0.03, 1.05)
ax_a.set_xlabel("Evolutionary time  $\\tau$")
ax_a.set_ylabel("D2-adopted share  $x_P(\\tau)$")

# Legend at UPPER-LEFT — above all rising trajectories before they reach
# y ≈ 0.55 (which happens around τ ≈ 22 for the steepest f=0.20 curve).
ax_a.legend(loc='upper left', bbox_to_anchor=(0.015, 0.98),
            ncol=1, fontsize=6.5, handlelength=1.5,
            labelspacing=0.30, frameon=False)
panel_label(ax_a, "(a)", x=-0.06, y=1.09)

# ── Panel (b): provincial payoff differential Δπ_P(f) ─────────
f_grid = np.linspace(0, 1, 400)
dpi_grid = delta_pi_P(f_grid)

# Sign-shaded regions: blue tint = D2 favored, red tint = status quo favored
ax_b.fill_between(f_grid, 0, dpi_grid, where=(dpi_grid > 0),
                  color=C_LLBLUE, alpha=0.95,
                  label="$\\Delta\\pi_P > 0$:  D2 is ESS")
ax_b.fill_between(f_grid, 0, dpi_grid, where=(dpi_grid < 0),
                  color=C_LRED, alpha=0.45,
                  label="$\\Delta\\pi_P < 0$:  status quo is ESS")

# Payoff differential curve
ax_b.plot(f_grid, dpi_grid, color=C_NAVY, lw=1.4)

# Zero-crossing & f* marker
ax_b.axhline(0, color=C_MGRAY, lw=0.5, ls='-')
ax_b.axvline(F_STAR, color=C_BLACK, lw=0.9, ls='--', alpha=0.85, zorder=2)
ax_b.scatter([F_STAR], [0], s=24, color=C_BLACK,
             edgecolors=C_BLACK, linewidths=0.7, zorder=5)

# f* label
ax_b.text(F_STAR + 0.02, 0.012, f"$f^* = {F_STAR:.3f}$",
          fontsize=7, color=C_BLACK, fontweight='bold', va='bottom')

ax_b.set_xlim(0, 1)
ax_b.set_ylim(-0.12, 0.22)
ax_b.set_xlabel("County fiscal autonomy  $f$")
ax_b.set_ylabel("$\\Delta\\pi_P(f)$,  provincial payoff differential")

# Legend at LOWER-LEFT in the empty white region below y=0 at low f
# (the f* dashed line is at f=0.667 — outside this region).
ax_b.legend(loc='lower left', bbox_to_anchor=(0.02, 0.02),
            fontsize=6.2, handlelength=1.4,
            labelspacing=0.30, frameon=False)
panel_label(ax_b, "(b)", x=-0.16, y=1.10)

# ── Panel (c): empirical density vs f* ───────────────────────
df = pd.read_stata("data/analysis/panel_analysis_public.dta")
df = df.sort_values(["county_code", "year"]).reset_index(drop=True)

def compute_pre_fa(group):
    d2y = group["D2_year"].iloc[0] if not group["D2_year"].isna().all() else None
    if d2y is None or pd.isna(d2y):
        sub = group.head(3)
    else:
        sub = group[(group["year"] >= d2y - 3) & (group["year"] < d2y)]
    fa = sub["fiscal_autonomy"].dropna()
    return fa.mean() if len(fa) > 0 else np.nan

pre_fa = (df.groupby("county_code", group_keys=False)
            .apply(compute_pre_fa, include_groups=False)
            .dropna())
n_counties = len(pre_fa)
mean_fa    = float(pre_fa.mean())
share_below = float((pre_fa < F_STAR).mean()) * 100

# Clip for visualization
pre_fa_clip = pre_fa.clip(0, 1.5)
kde = gaussian_kde(pre_fa_clip, bw_method=0.25)
x_grid = np.linspace(0, 1.5, 600)
density = kde(x_grid)

# Light blue shading for the f<f* (D2-ESS) region only
mask_below = x_grid <= F_STAR
ax_c.fill_between(x_grid[mask_below], 0, density[mask_below],
                  color=C_LLBLUE, alpha=0.95, zorder=1,
                  label=f"D2-ESS regime  ($f<f^*$):  {share_below:.0f}% of sample")

# Density curve overlay
ax_c.plot(x_grid, density, color=C_NAVY, lw=1.3, zorder=3)

# f* and f̄ dashed lines: truncated at 85% of their density-curve heights so
# their tops sit BELOW the curve and well clear of the upper-right legend.
density_at_fstar = float(kde(np.array([F_STAR]))[0])
density_at_mean  = float(kde(np.array([mean_fa]))[0])

ax_c.vlines(F_STAR, 0, density_at_fstar * 0.95,
            color=C_BLACK, lw=1.0, ls='--', zorder=2,
            label=f"ESS threshold  $f^* = {F_STAR:.3f}$")
ax_c.vlines(mean_fa, 0, density_at_mean * 0.85,
            color=C_RED, lw=1.0, ls='--', zorder=2,
            label=f"Sample mean  $\\bar f = {mean_fa:.3f}$")

ymax = density.max()
# (Inline f* and f̄ value labels removed — meanings are now in the legend.)

# PolicyTree leaf threshold — triangle marker on the x-axis only.
# Meaning is conveyed via the legend (matplotlib auto-uses the marker as
# the legend handle when label= is set on the scatter call).
LEAF = 0.049
ax_c.scatter([LEAF], [0], color=C_BLACK, marker='^', s=30,
             zorder=5, clip_on=False,
             label=f"PolicyTree leaf cut  $f = {LEAF}$")

ax_c.set_xlim(0, 1.2)
# Extra headroom above the density peak so the legend at upper-right sits
# clearly ABOVE the dashed-line tops (which end at ~0.85× peak).
ax_c.set_ylim(0, ymax * 1.50)
ax_c.set_xlabel("Pre-reform fiscal autonomy  $f$")
ax_c.set_ylabel(f"Empirical density  ($N={n_counties:,}$)")

# Legend at UPPER-RIGHT corner: density tail is low there (f>0.9, density<0.4),
# clear of both the f̄ line (f=0.383) and the f* line (f=0.667), and clear
# of the f̄ and f* inline labels (which sit near their respective dashed lines).
ax_c.legend(loc='upper right', bbox_to_anchor=(0.99, 0.99),
            fontsize=6.2, handlelength=1.4,
            labelspacing=0.30, frameon=False)
panel_label(ax_c, "(c)", x=-0.16, y=1.10)

# ── Save (PDF + PNG) — no suptitle, by design ─────────────────
out_pdf = "outputs/figures/fig1_evolutionary_game.pdf"
out_png = "outputs/figures/fig1_evolutionary_game.png"
fig.savefig(out_pdf, dpi=300, bbox_inches='tight')
fig.savefig(out_png, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"  fig1_evolutionary_game  ✓  → {out_pdf}")
print(f"  N counties (panel c): {n_counties}")
print(f"  share f<f*: {share_below:.1f}%")
print(f"  mean f̄: {mean_fa:.3f}")
