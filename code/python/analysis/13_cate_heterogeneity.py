"""
T13: CATE 异质性正式统计检验
验证博弈论 Proposition 1: 低财政自主度县受到改革的 CATE 更大（负相关）
"""

import sys
import os
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.abspath('.'))

np.random.seed(42)

# ── 1. 读取数据 ────────────────────────────────────────────────────────────────
d2 = pd.read_csv('data/processed/d2_cate_results.csv')
grf = pd.read_csv('data/processed/grf_input.csv')

df = d2.merge(grf[['county_code', 'fiscal_autonomy_pre', 'region_val',
                    'ln_gdppc_outcome', 'gov_scale_pre', 'ln_pop_pre']],
              on='county_code', how='inner')

print(f"合并后样本量: {len(df)}")
print(f"CATE 描述统计:\n{df['cate'].describe()}")
print(f"fiscal_autonomy_pre 描述统计:\n{df['fiscal_autonomy_pre'].describe()}")
print(f"region_val 分布:\n{df['region_val'].value_counts().sort_index()}")

# ── 2. 检验1：异质性 t 检验 ────────────────────────────────────────────────────
median_cate = df['cate'].median()
high_cate = df[df['cate'] >= median_cate]['fiscal_autonomy_pre'].dropna()
low_cate  = df[df['cate'] <  median_cate]['fiscal_autonomy_pre'].dropna()

t1, p1 = stats.ttest_ind(high_cate, low_cate, equal_var=False)
mean_high = high_cate.mean()
mean_low  = low_cate.mean()

print("\n===== 检验1: 高/低 CATE 组 fiscal_autonomy_pre t 检验 =====")
print(f"  高CATE组 (≥中位数) 均值: {mean_high:.4f}  (n={len(high_cate)})")
print(f"  低CATE组 (<中位数) 均值: {mean_low:.4f}  (n={len(low_cate)})")
print(f"  t = {t1:.4f},  p = {p1:.6f}")
if mean_high < mean_low:
    print("  → 方向符合预测：高CATE组财政自主度更低")
else:
    print("  → 方向与预测相反：高CATE组财政自主度更高，需注意")

# ── 3. 检验2：Pearson 相关 ─────────────────────────────────────────────────────
valid = df[['cate', 'fiscal_autonomy_pre']].dropna()
r2, p2 = stats.pearsonr(valid['cate'], valid['fiscal_autonomy_pre'])

print("\n===== 检验2: Pearson 相关（CATE ~ fiscal_autonomy_pre） =====")
print(f"  r = {r2:.4f},  p = {p2:.6f}")
if r2 < 0:
    print("  → r < 0，支持博弈论预测（低自主度→高CATE）")
else:
    print("  ★ 注意: r > 0，与博弈论预测不一致，需要解释 ★")

# ── 4. 检验3：地区分组 ANOVA ───────────────────────────────────────────────────
region_groups = {}
region_labels = {1: '东部', 2: '中部', 3: '西部'}
for rv in [1, 2, 3]:
    grp = df[df['region_val'] == rv]['cate'].dropna()
    region_groups[rv] = grp

f3, p3 = stats.f_oneway(*[region_groups[rv] for rv in [1, 2, 3]])

print("\n===== 检验3: 地区 CATE ANOVA =====")
region_stats = {}
for rv in [1, 2, 3]:
    grp = region_groups[rv]
    se = grp.std() / np.sqrt(len(grp))
    region_stats[rv] = {'mean': grp.mean(), 'se': se, 'n': len(grp),
                        'ci_low': grp.mean() - 1.96*se, 'ci_hi': grp.mean() + 1.96*se}
    print(f"  {region_labels[rv]}({rv}): 均值={grp.mean():.4f}, SE={se:.4f}, "
          f"95%CI=[{grp.mean()-1.96*se:.4f}, {grp.mean()+1.96*se:.4f}], n={len(grp)}")
print(f"  F = {f3:.4f},  p = {p3:.6f}")

# ── 5. 检验4：单变量 GRF 估计（Bootstrap heterogeneity test） ──────────────────
print("\n===== 检验4: 单变量 GRF（fiscal_autonomy_pre）CATE 方向 =====")
try:
    from econml.grf import CausalForest
    # 用 D2 treated 的样本
    sub = df[['cate', 'fiscal_autonomy_pre', 'ln_gdppc_outcome',
              'gov_scale_pre', 'ln_pop_pre', 'D2']].dropna()

    # 以 fiscal_autonomy_pre 为唯一协变量，用 CATE 作为 Y，D2 作为 T
    # 这里是单变量 GRF：X = fiscal_autonomy_pre，Y = CATE（伪结果）
    # 更严格的做法：重新估计以 fiscal_autonomy_pre 为协变量的 CausalForest
    X4 = sub[['fiscal_autonomy_pre']].values
    # 用 standardized CATE 作结果
    Y4 = sub['ln_gdppc_outcome'].values
    W4 = sub['D2'].values

    cf4 = CausalForest(n_estimators=200, random_state=42, n_jobs=-1)
    cf4.fit(X4, W4, Y4)
    cate4 = cf4.predict(X4).flatten()

    # 与 fiscal_autonomy_pre 的相关方向
    r4, p4 = stats.pearsonr(cate4, sub['fiscal_autonomy_pre'].values)
    print(f"  单变量 GRF (X=fiscal_autonomy_pre) ATE = {cate4.mean():.4f}")
    print(f"  CATE ~ fiscal_autonomy_pre: r = {r4:.4f}, p = {p4:.6f}")
    if r4 < 0:
        print("  → 单变量 GRF 确认：低财政自主度→更高 CATE，支持博弈论")
    else:
        print("  ★ 单变量 GRF: r > 0，与博弈论预测不一致")
    test4_r = r4
    test4_p = p4
    test4_ate = cate4.mean()
    test4_success = True
except Exception as e:
    print(f"  单变量 GRF 失败: {e}")
    # 备选：OLS 回归斜率作为效应方向指示
    from scipy.stats import linregress
    slope, intercept, r4_alt, p4_alt, se_slope = linregress(
        df['fiscal_autonomy_pre'].dropna(), df['cate'].dropna()
    )
    print(f"  备选 OLS 斜率: beta = {slope:.6f}, r = {r4_alt:.4f}, p = {p4_alt:.6f}")
    test4_r = r4_alt
    test4_p = p4_alt
    test4_ate = slope
    test4_success = False

# ── 6. 可视化 fig3: CATE 按 fiscal_autonomy_pre 四分位组 ──────────────────────
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 11

df['fiscal_q'] = pd.qcut(df['fiscal_autonomy_pre'], q=4,
                          labels=['Q1\n(lowest)', 'Q2', 'Q3', 'Q4\n(highest)'])

fig3_data = df.groupby('fiscal_q', observed=True)['cate'].agg(['mean', 'sem']).reset_index()
fig3_data.columns = ['fiscal_q', 'mean_cate', 'se_cate']

fig, ax = plt.subplots(figsize=(7, 5))
colors = ['#d73027', '#fc8d59', '#91bfdb', '#4575b4']
bars = ax.bar(fig3_data['fiscal_q'].astype(str), fig3_data['mean_cate'],
              yerr=1.96 * fig3_data['se_cate'],
              capsize=5, color=colors, edgecolor='black', linewidth=0.8,
              error_kw=dict(elinewidth=1.2, ecolor='black'))

ax.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
ax.set_xlabel('Fiscal Autonomy Quartile (Pre-Reform)', fontsize=12)
ax.set_ylabel('Mean CATE (Log GDP per capita growth)', fontsize=12)
ax.set_title('Figure 3: CATE Distribution by Fiscal Autonomy Quartile', fontsize=13, pad=10)
ax.text(0.02, 0.97,
        f'Note: Error bars = 95% CI\nPearson r(CATE, fiscal_autonomy) = {r2:.3f} (p={p2:.4f})',
        transform=ax.transAxes, fontsize=9, va='top', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
plt.tight_layout()
plt.savefig('outputs/figures/fig3_cate_distribution.pdf', dpi=300, bbox_inches='tight')
plt.savefig('outputs/figures/fig3_cate_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("\n保存 fig3_cate_distribution.pdf")

# ── 7. 可视化 fig4: 散点图 CATE vs fiscal_autonomy_pre ────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))

# 按地区上色
region_colors = {1: '#d62728', 2: '#1f77b4', 3: '#2ca02c'}
region_labels_plot = {1: 'Eastern', 2: 'Central', 3: 'Western'}

for rv in [1, 2, 3]:
    sub_r = df[df['region_val'] == rv]
    ax.scatter(sub_r['fiscal_autonomy_pre'], sub_r['cate'],
               alpha=0.35, s=18, color=region_colors[rv],
               label=region_labels_plot[rv], edgecolors='none')

# OLS 拟合线（全样本）
valid2 = df[['fiscal_autonomy_pre', 'cate']].dropna()
slope_ols, intercept_ols, _, _, _ = stats.linregress(
    valid2['fiscal_autonomy_pre'], valid2['cate'])
x_line = np.linspace(valid2['fiscal_autonomy_pre'].min(),
                     valid2['fiscal_autonomy_pre'].max(), 100)
y_line = slope_ols * x_line + intercept_ols
ax.plot(x_line, y_line, color='black', linewidth=2, linestyle='-',
        label=f'OLS fit (slope={slope_ols:.4f})')

ax.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.6)

ax.set_xlabel('Pre-Reform Fiscal Autonomy (fiscal_autonomy_pre)', fontsize=12)
ax.set_ylabel('Estimated CATE (CausalForest)', fontsize=12)
ax.set_title('Figure 4: CATE vs. Fiscal Autonomy\n(D2: County Finance to Provincial Management)',
             fontsize=12, pad=8)

direction_note = f'Pearson r = {r2:.3f}, p = {p2:.4f}'
if r2 < 0:
    direction_note += '\n→ Negative correlation: supports game theory prediction'
else:
    direction_note += '\n★ Positive correlation: INCONSISTENT with game theory prediction'

ax.text(0.02, 0.97, direction_note,
        transform=ax.transAxes, fontsize=9, va='top',
        bbox=dict(boxstyle='round,pad=0.3',
                  facecolor='lightyellow' if r2 < 0 else 'lightsalmon',
                  alpha=0.85))

handles, labels_leg = ax.get_legend_handles_labels()
ax.legend(handles, labels_leg, fontsize=9, loc='upper right')
plt.tight_layout()
plt.savefig('outputs/figures/fig4_cate_by_fiscal.pdf', dpi=300, bbox_inches='tight')
plt.savefig('outputs/figures/fig4_cate_by_fiscal.png', dpi=300, bbox_inches='tight')
plt.close()
print("保存 fig4_cate_by_fiscal.pdf")

# ── 8. 输出汇总 ────────────────────────────────────────────────────────────────
print("\n========== 最终结果汇总 ==========")
print(f"检验1 t = {t1:.4f}, p = {p1:.6f}, 高CATE组fiscal均值={mean_high:.4f}, 低CATE组={mean_low:.4f}")
print(f"检验2 Pearson r = {r2:.4f}, p = {p2:.6f}")
print(f"检验3 ANOVA F = {f3:.4f}, p = {p3:.6f}")
print(f"检验4 {'单变量GRF' if test4_success else 'OLS备选'} r = {test4_r:.4f}, p = {test4_p:.6f}")

# 写入 CSV 供报告引用
results_summary = {
    'test1_t': t1, 'test1_p': p1,
    'test1_mean_high_cate': mean_high, 'test1_mean_low_cate': mean_low,
    'test2_r': r2, 'test2_p': p2,
    'test3_F': f3, 'test3_p': p3,
    'test4_r': test4_r, 'test4_p': test4_p,
    'test4_method': 'single_var_GRF' if test4_success else 'OLS_fallback',
}
pd.DataFrame([results_summary]).to_csv('data/processed/t13_test_results.csv', index=False)
print("\n检验结果已保存到 data/processed/t13_test_results.csv")
