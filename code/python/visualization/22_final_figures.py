"""
22_final_figures.py  (v5 — 热力图版)
==============================================
  fig1_identification.pdf  - 事件研究动态效应 + 安慰剂检验
  fig2_heterogeneity.pdf   - CATE 异质性约束线
  fig3_robustness.pdf      - 区域异质性热力图
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, MultipleLocator
from scipy import stats
from sklearn.linear_model import LinearRegression

warnings.filterwarnings("ignore")
os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.makedirs("outputs/figures", exist_ok=True)

# ══════════════════════════════════════════════════════════════
# 调色板
# ══════════════════════════════════════════════════════════════
C_NAVY   = '#1B3F6E'
C_BLUE   = '#2E75B6'
C_LBLUE  = '#9FC5E8'
C_LLBLUE = '#D6E8F7'
C_RED    = '#C0392B'
C_LRED   = '#E8A89C'
C_GREEN  = '#1A6B3C'
C_ORANGE = '#B05000'
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
    'legend.fontsize':      6.5,
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


def panel_label(ax, label, x=-0.12, y=1.06, size=9):
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=size, fontweight='normal', va='top', ha='left',
            color=C_BLACK)


def save_fig(fig, stem):
    pdf = f"outputs/figures/{stem}.pdf"
    png = f"outputs/figures/{stem}.png"
    fig.savefig(pdf, dpi=300, bbox_inches='tight')
    fig.savefig(png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  {stem}  ✓  → {pdf}")
    return pdf


def _ols_ci(x_arr, y_arr, x_line, alpha=0.05):
    n      = len(x_arr)
    x_mean = float(x_arr.mean())
    reg    = LinearRegression().fit(x_arr.reshape(-1, 1), y_arr)
    y_fit  = reg.predict(x_line.reshape(-1, 1))
    y_pred = reg.predict(x_arr.reshape(-1, 1))
    mse    = float(np.mean((y_arr - y_pred) ** 2))
    se     = np.sqrt(mse * (1/n + (x_line - x_mean)**2 /
                            float(np.sum((x_arr - x_mean)**2))))
    t      = stats.t.ppf(1 - alpha/2, df=n - 2)
    return y_fit, y_fit - t * se, y_fit + t * se


# ══════════════════════════════════════════════════════════════
# 约束线分析辅助函数
# ══════════════════════════════════════════════════════════════
def _extract_envelope(x, y, bins=40):
    edges = np.linspace(x.min(), x.max(), bins + 1)
    vx, q95, q05 = [], [], []
    for i in range(bins):
        mask = (x >= edges[i]) & (x < edges[i + 1])
        if mask.sum() >= 12:
            vx.append(np.median(x[mask]))
            q95.append(np.percentile(y[mask], 95))
            q05.append(np.percentile(y[mask],  5))
    return np.array(vx), np.array(q95), np.array(q05)


def _fit_poly_auto(xp, yp):
    """自动选择 2 次或 3 次多项式（校正 R² 更高者）。"""
    n = len(xp)
    if n <= 5:
        return np.poly1d([float(yp.mean())]), 0.0
    best_p, best_r2 = None, -np.inf
    for deg in (2, 3):
        c  = np.polyfit(xp, yp, deg)
        p  = np.poly1d(c)
        ss_res = float(np.sum((yp - p(xp)) ** 2))
        ss_tot = float(np.sum((yp - yp.mean()) ** 2))
        r2     = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        adj_r2 = 1 - (1 - r2) * (n - 1) / max(n - deg - 1, 1)
        if adj_r2 > best_r2:
            best_r2, best_p = adj_r2, (p, r2)
    return best_p


def _bootstrap_ci(x, y, x_sm, is_upper=True, bins=40, n_boot=200, seed=42):
    rng  = np.random.default_rng(seed)
    n    = len(x)
    bank = np.full((n_boot, len(x_sm)), np.nan)
    ok   = 0
    for _ in range(n_boot):
        idx  = rng.integers(0, n, size=n)
        xb, yb = x[idx], y[idx]
        edges = np.linspace(xb.min(), xb.max(), bins + 1)
        vx, qv = [], []
        for i in range(bins):
            m = (xb >= edges[i]) & (xb < edges[i + 1])
            if m.sum() >= 12:
                vx.append(np.median(xb[m]))
                qv.append(np.percentile(yb[m], 95 if is_upper else 5))
        if len(vx) <= 5:
            continue
        try:
            p, _ = _fit_poly_auto(np.array(vx), np.array(qv))
            bank[ok] = p(x_sm)
            ok += 1
        except Exception:
            continue
    if ok == 0:
        nan = np.full_like(x_sm, np.nan)
        return nan, nan
    bank = bank[:ok]
    return np.nanpercentile(bank, 2.5, axis=0), np.nanpercentile(bank, 97.5, axis=0)


def _find_extreme(poly, x_min, x_max, find_max=True):
    deriv = poly.deriv()
    roots = np.roots(deriv.coeffs)
    real_roots = roots[np.isreal(roots)].real
    span = x_max - x_min
    valid = real_roots[
        (real_roots > x_min + 0.01 * span) &
        (real_roots < x_max - 0.01 * span)
    ]
    if len(valid) == 0:
        return None, None
    y_vals = poly(valid)
    idx = np.argmax(y_vals) if find_max else np.argmin(y_vals)
    return float(valid[idx]), float(y_vals[idx])


def _draw_constraint(ax, x_all, y_all, xlabel, panel_lbl,
                     c_up=C_RED, c_lo=C_BLUE, bins=40, n_boot=200,
                     pct_clip=2, ylim=None, show_legend=False):
    """在 ax 上绘制双约束线图（上/下边界 + Bootstrap CI）。
    pct_clip: 两端裁剪百分位（去除极端值防多项式发散）。
    """
    # ── 截断极端值
    xlo = np.percentile(x_all, pct_clip)
    xhi = np.percentile(x_all, 100 - pct_clip)
    mask = (x_all >= xlo) & (x_all <= xhi)
    x_use = x_all[mask]
    y_use = y_all[mask]

    x_min, x_max = float(x_use.min()), float(x_use.max())
    vx, q95, q05 = _extract_envelope(x_use, y_use, bins=bins)

    p_up, r2_up = _fit_poly_auto(vx, q95)
    p_lo, r2_lo = _fit_poly_auto(vx, q05)

    x_sm = np.linspace(x_min, x_max, 200)
    y_clip_lo = ylim[0] * 1.5 if ylim else -np.inf
    y_clip_hi = ylim[1] * 1.5 if ylim else  np.inf
    y_up = np.clip(p_up(x_sm), y_clip_lo, y_clip_hi)
    y_lo = np.clip(p_lo(x_sm), y_clip_lo, y_clip_hi)

    ci_up_lo, ci_up_hi = _bootstrap_ci(x_use, y_use, x_sm, is_upper=True,  bins=bins, n_boot=n_boot)
    ci_lo_lo, ci_lo_hi = _bootstrap_ci(x_use, y_use, x_sm, is_upper=False, bins=bins, n_boot=n_boot)

    # 背景散点
    ax.scatter(x_use, y_use, color=C_LGRAY, alpha=0.14, s=3, zorder=1, linewidths=0)

    # CI 带（先画，曲线盖在上面）
    ax.fill_between(x_sm,
                    np.clip(ci_up_lo, y_clip_lo, y_clip_hi),
                    np.clip(ci_up_hi, y_clip_lo, y_clip_hi),
                    color=c_up, alpha=0.10, zorder=2)
    ax.fill_between(x_sm,
                    np.clip(ci_lo_lo, y_clip_lo, y_clip_hi),
                    np.clip(ci_lo_hi, y_clip_lo, y_clip_hi),
                    color=c_lo, alpha=0.10, zorder=2)

    # 拟合曲线
    ax.plot(x_sm, y_up, color=c_up, lw=1.6, zorder=4)
    ax.plot(x_sm, y_lo, color=c_lo, lw=1.6, zorder=4)

    # 极值点：只画空心圆，不加虚线
    for find_max, poly, col in [(True, p_up, c_up), (False, p_lo, c_lo)]:
        tx, ty = _find_extreme(poly, x_min, x_max, find_max=find_max)
        if tx is None:
            continue
        ty_c = float(np.clip(ty, y_clip_lo, y_clip_hi))
        if ylim and not (ylim[0] <= ty_c <= ylim[1]):
            continue
        ax.scatter([tx], [ty_c], s=24, color='white',
                   edgecolors=col, linewidths=1.1, zorder=5)

    ax.axhline(0, color=C_MGRAY, lw=0.5, ls='--', zorder=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("CATE, D2 reform (pp)")
    if ylim:
        ax.set_ylim(ylim)
    ax.yaxis.set_major_locator(MultipleLocator(0.03))
    ax.xaxis.set_major_locator(MaxNLocator(5))

    # 图内图例
    leg = [
        Line2D([0], [0], color=c_up, lw=1.6,
               label=f'95th pct  $R^2$={r2_up:.2f}'),
        Line2D([0], [0], color=c_lo, lw=1.6,
               label=f'5th pct    $R^2$={r2_lo:.2f}'),
    ]
    ax.legend(handles=leg, loc='upper left', fontsize=5.2,
              handlelength=1.0, borderpad=0.3, labelspacing=0.20,
              frameon=False)
    panel_label(ax, panel_lbl, x=-0.16, y=1.14)


def _prep_es(df, ref_period=0):
    """确保基准期存在，返回排序后 DataFrame。"""
    df = df.copy()
    if ref_period not in df['period'].values:
        ref = pd.DataFrame([{'period': ref_period, 'coef': 0,
                              'ci_lower': 0, 'ci_upper': 0, 'se': 0}])
        df = pd.concat([df, ref])
    return df.sort_values('period').reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# FIGURE 1  主效应 + 平行趋势检验（1x2布局）
# ══════════════════════════════════════════════════════════════
def fig1_identification():
    """主效应比较 + 平行趋势检验"""
    twfe      = pd.read_csv("data/processed/es_twfe.csv")
    sunab     = pd.read_csv("data/processed/es_sunab.csv").rename(
        columns={'se': 'ci_lower', 'ci_lower': 'ci_upper', 'ci_upper': 'se'})
    did2s     = pd.read_csv("data/processed/es_did2s.csv")
    lngdppc   = pd.read_csv("data/processed/es_ln_gdppc.csv")
    fiscal    = pd.read_csv("data/processed/es_fiscal_autonomy.csv")
    fiscalrev = pd.read_csv("data/processed/es_fiscal_rev_pc.csv")

    twfe      = _prep_es(twfe[twfe['period'].between(-5, 10)])
    sunab     = _prep_es(sunab[sunab['period'].between(-5, 10)])
    did2s     = _prep_es(did2s[did2s['period'].between(-5, 10)])
    lngdppc   = _prep_es(lngdppc[lngdppc['period'].between(-5, 10)])
    fiscal    = _prep_es(fiscal[fiscal['period'].between(-5, 10)])
    fiscalrev = _prep_es(fiscalrev[fiscalrev['period'].between(-5, 10)])

    # 改革参考年份
    REF_YEAR = 2009

    # 1x2 布局
    fig = plt.figure(figsize=(FIG_WIDTH, 3.4))
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.28)

    # ===================== 左面板：主效应比较 =====================
    ax_left = fig.add_subplot(gs[0, 0])

    jit = 0.18

    # Gardner (深蓝) - 误差棒箱体
    d1 = did2s
    x1 = d1['period'].values - jit
    for xi, ci_lo, ci_hi in zip(x1, d1['ci_lower'], d1['ci_upper']):
        ax_left.fill_between([xi-0.06, xi+0.06], [ci_lo, ci_lo], [ci_hi, ci_hi],
                             color=C_NAVY, alpha=0.15, zorder=1)
    ax_left.scatter(x1, d1['coef'].values, s=18, color='white', edgecolors=C_NAVY,
                    linewidths=0.8, zorder=4, marker='o')
    ax_left.plot([], [], 'o-', color=C_NAVY, ms=4, lw=1.2, label='Two-stage')

    # Sun-Abraham (浅蓝) - 误差棒箱体
    d2 = sunab
    x2 = d2['period'].values + jit
    for xi, ci_lo, ci_hi in zip(x2, d2['ci_lower'], d2['ci_upper']):
        ax_left.fill_between([xi-0.06, xi+0.06], [ci_lo, ci_lo], [ci_hi, ci_hi],
                             color=C_BLUE, alpha=0.15, zorder=1)
    ax_left.scatter(x2, d2['coef'].values, s=18, color='white', edgecolors=C_BLUE,
                    linewidths=0.8, zorder=4, marker='s')
    ax_left.plot([], [], 's-', color=C_BLUE, ms=4, lw=1.2, label='Interaction-weighted')

    ax_left.axhline(0, color=C_MGRAY, lw=0.6, zorder=0)

    # 相对年份标签
    periods = sorted(d1['period'].unique())
    ax_left.set_xticks(periods)
    ax_left.set_xticklabels([str(int(p)) for p in periods], fontsize=7)

    ax_left.set_ylabel("ATT (pp)", fontsize=7)
    ax_left.set_xlabel("Years relative to reform", fontsize=7)
    ax_left.tick_params(axis='y', labelsize=6.5)
    ax_left.legend(loc='upper left', fontsize=6.5, frameon=False, handletextpad=0.5,
                   title=f'Baseline: {REF_YEAR}', title_fontsize=6)
    panel_label(ax_left, "(a)", x=-0.08, y=1.06)

    # ===================== 右面板：2个安慰剂变量（归一化）=====================
    ax_right = fig.add_subplot(gs[0, 1])

    # 归一化函数
    def normalize(y):
        y = np.array(y)
        ymax = np.max(np.abs(y))
        return y / ymax if ymax > 0 else y

    jit2 = 0.22
    markers = ['o', 's']
    colors = [C_RED, C_GREEN]
    labels = ['Fiscal rev. pc', 'GDP growth']

    # 加载GDP增长率
    gdpg = pd.read_csv("data/processed/es_gdp_growth.csv")
    gdpg = _prep_es(gdpg[gdpg['period'].between(-5, 10)])

    datasets = [
        (fiscalrev['period'].values - jit2, fiscalrev['coef'].values, fiscalrev['ci_lower'], fiscalrev['ci_upper']),
        (gdpg['period'].values + jit2, gdpg['coef'].values, gdpg['ci_lower'], gdpg['ci_upper']),
    ]

    for i, (x, y, ci_lo, ci_hi) in enumerate(datasets):
        y_norm = normalize(y)
        ci_lo_norm = normalize(ci_lo)
        ci_hi_norm = normalize(ci_hi)

        # 箱体
        for xi, ylo, yhi in zip(x, ci_lo_norm, ci_hi_norm):
            ax_right.fill_between([xi-0.05, xi+0.05], [ylo, ylo], [yhi, yhi],
                                  color=colors[i], alpha=0.15, zorder=1)
        # 点估计
        ax_right.scatter(x, y_norm, s=16, color='white', edgecolors=colors[i],
                         linewidths=0.7, zorder=4, marker=markers[i])
        # 图例线
        ax_right.plot([], [], f'{markers[i]}-', color=colors[i], ms=4, lw=1.0, label=labels[i])

    ax_right.axhline(0, color=C_MGRAY, lw=0.6, zorder=0)
    ax_right.set_xticks(periods)
    ax_right.set_xticklabels([str(int(p)) for p in periods], fontsize=7)
    ax_right.set_ylim(-2, 3)
    ax_right.set_ylabel("Normalized ATT", fontsize=7)
    ax_right.set_xlabel("Years relative to reform", fontsize=7)
    ax_right.tick_params(axis='y', labelsize=6.5)
    ax_right.legend(loc='upper left', fontsize=6.5, frameon=False, handletextpad=0.5,
                   title=f'Baseline: {REF_YEAR}', title_fontsize=6)
    panel_label(ax_right, "(b)", x=-0.08, y=1.06)

    fig.tight_layout(pad=0.3)
    return save_fig(fig, "fig1_identification")


# ══════════════════════════════════════════════════════════════
# FIGURE 2  CATE 异质性：6 变量约束线（3×2）
# ══════════════════════════════════════════════════════════════
def fig2_heterogeneity():
    import pyreadstat
    grf  = pd.read_csv("data/processed/grf_input.csv")
    d2   = pd.read_csv("data/processed/d2_cate_results.csv")

    # 从主数据计算额外改革前均值（2005年前）
    raw, _ = pyreadstat.read_dta(
        "data/analysis/panel_analysis_public.dta",
        usecols=['county_code', 'year', 'fiscal_rev_pc', 'gdppc',
                 'transfer_dependence'])
    extra_pre = (raw[raw['year'] <= 2005]
                 .groupby('county_code')[['fiscal_rev_pc', 'gdppc', 'transfer_dependence']]
                 .mean()
                 .reset_index()
                 .rename(columns={'fiscal_rev_pc':       'fiscal_rev_pc_pre',
                                  'gdppc':               'gdppc_pre',
                                  'transfer_dependence': 'transfer_dep_pre'}))

    need_cols = ['county_code', 'fiscal_autonomy_pre', 'secondary_ratio_pre',
                 'primary_ratio_pre', 'gov_scale_pre']
    df = (grf[need_cols]
          .merge(d2[['county_code', 'cate']], on='county_code', how='inner')
          .merge(extra_pre, on='county_code', how='left')
          .dropna(subset=['fiscal_autonomy_pre', 'secondary_ratio_pre',
                          'primary_ratio_pre', 'gov_scale_pre', 'cate']))

    Y_LIM = (-0.10, 0.04)
    C_UP  = C_RED
    C_LO  = C_BLUE

    PANELS = [
        ('fiscal_autonomy_pre',  'Fiscal autonomy (pre-reform)',   '(a)'),
        ('transfer_dep_pre',     'Transfer dependence (pre-reform)', '(b)'),
        ('secondary_ratio_pre',  'Secondary industry share (pre-reform)', '(c)'),
        ('primary_ratio_pre',    'Primary industry share (pre-reform)',   '(d)'),
        ('fiscal_rev_pc_pre',   'Fiscal revenue per capita (pre-reform)', '(e)'),
        ('gdppc_pre',           'GDP per capita (pre-reform)',    '(f)'),
    ]

    fig = plt.figure(figsize=(FIG_WIDTH, 4.6))
    gs  = gridspec.GridSpec(2, 3, figure=fig, wspace=0.58, hspace=0.52)

    for idx, (xvar, xlabel, lbl) in enumerate(PANELS):
        r, c = divmod(idx, 3)
        ax = fig.add_subplot(gs[r, c])
        _draw_constraint(ax,
                         df[xvar].values,
                         df['cate'].values,
                         xlabel=xlabel,
                         panel_lbl=lbl,
                         c_up=C_UP, c_lo=C_LO,
                         pct_clip=2, ylim=Y_LIM)
        if c != 0:
            ax.set_ylabel("")

    fig.tight_layout(pad=0.5)
    return save_fig(fig, "fig2_heterogeneity")


# ══════════════════════════════════════════════════════════════
# FIGURE 3  CATE 区域异质性驱动因子热力图
# ══════════════════════════════════════════════════════════════
def fig3_robustness():
    """区域异质性驱动因素 - 单热力图 + 合并条形图"""
    import pyreadstat
    import statsmodels.api as sm
    from sklearn.preprocessing import StandardScaler
    import matplotlib.colors as mcolors

    # 数据加载
    grf = pd.read_csv("data/processed/grf_input.csv")
    d2 = pd.read_csv("data/processed/d2_cate_results.csv")

    raw, _ = pyreadstat.read_dta(
        "data/analysis/panel_analysis_public.dta",
        usecols=['county_code', 'year', 'fiscal_rev_pc', 'gdppc', 'transfer_dependence'])
    extra = (raw[raw['year'] <= 2005]
             .groupby('county_code')[['fiscal_rev_pc', 'gdppc', 'transfer_dependence']]
             .mean().reset_index()
             .rename(columns={'fiscal_rev_pc': 'fiscal_rev_pc_pre', 'gdppc': 'gdppc_pre',
                            'transfer_dependence': 'transfer_dep_pre'}))

    need = ['county_code', 'fiscal_autonomy_pre', 'secondary_ratio_pre',
            'primary_ratio_pre', 'ln_pop_pre', 'region_val']
    df = grf[need].merge(d2[['county_code', 'cate']], on='county_code', how='inner').merge(
        extra, on='county_code', how='left').dropna()

    pred_vars = ['fiscal_autonomy_pre', 'transfer_dep_pre', 'fiscal_rev_pc_pre',
                'secondary_ratio_pre', 'primary_ratio_pre', 'gdppc_pre', 'ln_pop_pre']
    pred_labels = ['Fiscal autonomy', 'Transfer dep.', 'Fiscal rev.pc',
                  'Secondary ratio', 'Primary ratio', 'GDP per capita', 'Population (ln)']

    REGIONS = [(1, 'East'), (2, 'Central'), (3, 'West')]

    # 存储每个区域结果
    region_results = {}
    scaler = StandardScaler()
    for rval, rname in REGIONS:
        sub = df[df['region_val'] == rval].dropna(subset=pred_vars + ['cate'])
        if len(sub) < 20:
            region_results[rname] = None
            continue
        Xs = scaler.fit_transform(sub[pred_vars])
        ys = (sub['cate'].values - sub['cate'].mean()) / sub['cate'].std()
        model = sm.OLS(ys, sm.add_constant(Xs)).fit()
        region_results[rname] = {
            'n': len(sub),
            'coef': model.params[1:],
            'se': model.bse[1:],
            'pval': model.pvalues[1:],
            'conf_int': model.conf_int()[1:]
        }

    # 构建矩阵
    all_coefs = []
    all_sigs = []
    for rval, rname in REGIONS:
        res = region_results.get(rname)
        if res:
            all_coefs.append(res['coef'])
            all_sigs.append(res['pval'] < 0.05)
        else:
            all_coefs.append(np.zeros(len(pred_vars)))
            all_sigs.append(np.zeros(len(pred_vars), dtype=bool))

    coef_matrix = np.array(all_coefs).T  # (7, 3)
    sig_matrix = np.array(all_sigs).T

    # 绘图：2行 × 2列布局
    # (a) 热力图 | (b) 合并条形图
    fig = plt.figure(figsize=(FIG_WIDTH, 3.5))
    gs = fig.add_gridspec(1, 2, hspace=0.35, wspace=0.40, width_ratios=[1.1, 1])

    # 颜色
    vmax = np.abs(coef_matrix).max()
    cmap = plt.cm.RdBu_r
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    # === (a) 热力图 ===
    ax_heat = fig.add_subplot(gs[0, 0])
    im = ax_heat.imshow(coef_matrix, cmap=cmap, norm=norm, aspect='auto')
    panel_label(ax_heat, "(a)")

    # 数值和显著性
    for i in range(len(pred_vars)):
        for j in range(3):
            val = coef_matrix[i, j]
            sig = sig_matrix[i, j]
            bg_val = norm(val)
            text_color = 'white' if bg_val < 0.3 or bg_val > 0.7 else 'black'
            text_str = f'{val:.2f}'
            if sig:
                text_str += '*'
            ax_heat.text(j, i, text_str, ha='center', va='center',
                       fontsize=5.5, fontweight='bold', color=text_color)

    ax_heat.set_xticks(range(3))
    ax_heat.set_xticklabels(['East\n(n=278)', 'Central\n(n=504)', 'West\n(n=479)'], fontsize=6)
    ax_heat.set_yticks(range(len(pred_vars)))
    ax_heat.set_yticklabels(pred_labels, fontsize=6)
    ax_heat.tick_params(axis='x', length=0)
    ax_heat.tick_params(axis='y', length=0)
    ax_heat.set_xlabel('Region', fontsize=7)

    # 颜色条
    cbar = fig.colorbar(im, ax=ax_heat, shrink=0.7, pad=0.02)
    cbar.set_label('Std. coef.', fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    # === (b) 合并条形图 ===
    ax_bar = fig.add_subplot(gs[0, 1])
    colors = {'East': '#2E86AB', 'Central': '#A23B72', 'West': '#F18F01'}
    y_pos_base = np.arange(len(pred_vars))
    bar_height = 0.22
    offset = {'East': -0.22, 'Central': 0, 'West': 0.22}

    for rname in ['East', 'Central', 'West']:
        res = region_results.get(rname)
        if res is None:
            continue
        y_pos = y_pos_base + offset[rname]
        for i in range(len(pred_vars)):
            color = colors[rname] if res['coef'][i] > 0 else '#C73E1D'
            ax_bar.barh(y_pos[i], res['coef'][i], height=bar_height, color=color,
                     alpha=0.85, edgecolor='white', linewidth=0.4,
                     label=rname if i == 0 else '')
            ci_lo, ci_hi = res['conf_int'][i]
            ax_bar.plot([ci_lo, ci_hi], [y_pos[i], y_pos[i]], color='black', linewidth=0.7)
            ax_bar.plot([ci_lo, ci_lo], [y_pos[i]-0.03, y_pos[i]+0.03], color='black', linewidth=0.7)
            ax_bar.plot([ci_hi, ci_hi], [y_pos[i]-0.03, y_pos[i]+0.03], color='black', linewidth=0.7)

    ax_bar.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax_bar.set_yticks(y_pos_base)
    ax_bar.set_yticklabels(pred_labels, fontsize=6)
    ax_bar.set_xlabel('Std. coefficient', fontsize=7)
    ax_bar.tick_params(axis='x', labelsize=5)
    ax_bar.set_xlim(-2, 2)
    ax_bar.set_xticks([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2])
    panel_label(ax_bar, "(b)")

    # 图例 - 放在左上角
    handles, labels = ax_bar.get_legend_handles_labels()
    ax_bar.legend(handles, labels, loc='upper left', fontsize=5.5, frameon=False)

    return save_fig(fig, "fig3_robustness")


# ══════════════════════════════════════════════════════════════
# 主程序
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("Generating figures  (v5 — heatmap)")
    print("=" * 60)
    results = []
    for fn, name in [
        (fig1_identification, 'fig1_identification'),
        (fig2_heterogeneity,  'fig2_heterogeneity'),
        (fig3_robustness,     'fig3_robustness'),
    ]:
        try:
            results.append(fn())
        except Exception as e:
            import traceback
            print(f"  [ERROR] {name}: {e}")
            traceback.print_exc()
            results.append(None)

    print("\n完成。")
