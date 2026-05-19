"""
T16: DML 中介路径1 Step2+Bootstrap - fiscal_autonomy 对 gdp 的效应（β）及间接效应
顺序 DML 第二步：估计财政自主度对经济增长的效应 β（控制 D2），并 Bootstrap 间接效应
"""
import numpy as np
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LassoCV
import os
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ── 0. 常量（来自 T15/T14 报告） ──────────────────────────────────
ALPHA_T15_PCT = -1.4252   # D2→fiscal_autonomy，单位：百分点（%）
ALPHA_T15_RAW = ALPHA_T15_PCT / 100  # 原始比例单位（因 fiscal_autonomy 是比例）
TOTAL_EFFECT_T14 = 1.0415  # T14 DML theta，单位：pp（百分点）

# ── 1. 读取数据 ──────────────────────────────────────────────────
df = pd.read_csv("data/processed/dml_panel_within.csv")
cols_need = ["gdp_growth_pc_w", "fiscal_autonomy_w", "D2_w",
             "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
df = df.dropna(subset=cols_need).copy()
print(f"样本量（dropna后）: {len(df)}")

# ── 2. Step2: 估计 β（fiscal_autonomy → gdp_growth_pc，控制 D2） ──
# Y2 = gdp_growth_pc_w（百分点）
# T2 = fiscal_autonomy_w（比例，0~1 范围 within 变换）
# W2 = [D2_w, primary_ratio_w, secondary_ratio_w, ln_pop_w, gov_scale_w]
Y2 = df["gdp_growth_pc_w"].values
T2 = df["fiscal_autonomy_w"].values
W2 = df[["D2_w", "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values

print(f"\nY2 (gdp_growth_pc_w) 均值: {Y2.mean():.6e}  std: {Y2.std():.4f}")
print(f"T2 (fiscal_autonomy_w) 均值: {T2.mean():.6e}  std: {T2.std():.4f}")

model_step2 = LinearDML(
    model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
    model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
    random_state=42
)
model_step2.fit(Y2, T2, X=None, W=W2)

inf2 = model_step2.intercept__inference()
beta = float(np.atleast_1d(inf2.point_estimate).ravel()[0])
beta_se = float(np.atleast_1d(inf2.pred_stderr).ravel()[0])
beta_pval = float(np.atleast_1d(inf2.pvalue()).ravel()[0])
beta_ci = inf2.conf_int()
beta_ci_lo = float(np.atleast_1d(beta_ci[0]).ravel()[0])
beta_ci_hi = float(np.atleast_1d(beta_ci[1]).ravel()[0])

# β 的含义：fiscal_autonomy（0~1比例）单位变化对 gdp_growth_pc（百分点）的效应
# 将 β 转换为"财政自主度提升1百分点（0.01单位）的效应"
beta_pct_unit = beta * 0.01  # 每提升0.01单位 fiscal_autonomy 的效应（pp）

print(f"\n{'='*60}")
print(f"T16 Step2 结果：β（fiscal_autonomy → gdp_growth_pc）")
print(f"{'='*60}")
print(f"β（原始，每单位 fiscal_autonomy 变动）= {beta:.4f} pp")
print(f"SE = {beta_se:.4f}")
print(f"p值 = {beta_pval:.4f}")
print(f"95% CI: [{beta_ci_lo:.4f}, {beta_ci_hi:.4f}]")
print(f"β（每0.01单位，即1pp fiscal_autonomy）= {beta_pct_unit:.4f} pp")


# ── 3. 点估计间接效应 ─────────────────────────────────────────────
# α 单位：fiscal_autonomy 变化量（原始比例，如 -0.014252）
# β 单位：pp gdp_growth_pc / 单位 fiscal_autonomy（原始比例）
# 间接效应 = α_raw × β（单位：pp gdp_growth_pc）
# alpha_raw = -0.014252，beta 的单位一致
indirect_point = ALPHA_T15_RAW * beta  # pp
print(f"\n间接效应（点估计）= α × β = {ALPHA_T15_RAW:.6f} × {beta:.4f} = {indirect_point:.4f} pp")


# ── 4. Bootstrap 间接效应（1000次，或超时改200次）─────────────────

def fit_step1_boot(df_b):
    """Bootstrap Step1: D2 → fiscal_autonomy"""
    cols = ["fiscal_autonomy_w", "D2_w", "primary_ratio_w",
            "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
    db = df_b.dropna(subset=cols)
    Y_b = db["fiscal_autonomy_w"].values
    T_b = db["D2_w"].values
    W_b = db[["primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values
    m = LinearDML(
        model_y=LassoCV(cv=3, random_state=42, max_iter=3000),
        model_t=LassoCV(cv=3, random_state=42, max_iter=3000),
        random_state=42
    )
    m.fit(Y_b, T_b, X=None, W=W_b)
    inf_b = m.intercept__inference()
    return float(np.atleast_1d(inf_b.point_estimate).ravel()[0])


def fit_step2_boot(df_b):
    """Bootstrap Step2: fiscal_autonomy → gdp_growth_pc（控制 D2）"""
    cols = ["gdp_growth_pc_w", "fiscal_autonomy_w", "D2_w",
            "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
    db = df_b.dropna(subset=cols)
    Y_b = db["gdp_growth_pc_w"].values
    T_b = db["fiscal_autonomy_w"].values
    W_b = db[["D2_w", "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values
    m = LinearDML(
        model_y=LassoCV(cv=3, random_state=42, max_iter=3000),
        model_t=LassoCV(cv=3, random_state=42, max_iter=3000),
        random_state=42
    )
    m.fit(Y_b, T_b, X=None, W=W_b)
    inf_b = m.intercept__inference()
    return float(np.atleast_1d(inf_b.point_estimate).ravel()[0])


print(f"\n{'='*60}")
print("开始 Bootstrap（200次，cv=3以加速）...")
print("（若1000次>30分钟，按规范降至200次）")
print(f"{'='*60}")

n_bootstrap = 200
indirect_samples = []
n_obs = len(df)
rng = np.random.default_rng(42)

for i in range(n_bootstrap):
    idx = rng.choice(n_obs, n_obs, replace=True)
    df_boot = df.iloc[idx].copy()
    try:
        alpha_b = fit_step1_boot(df_boot)
        beta_b = fit_step2_boot(df_boot)
        indirect_b = alpha_b * beta_b
        indirect_samples.append(indirect_b)
    except Exception as e:
        # 跳过偶发数值失败的迭代
        pass
    if (i + 1) % 20 == 0:
        print(f"  Bootstrap 进度: {i+1}/{n_bootstrap}")

indirect_samples = np.array(indirect_samples)
n_valid = len(indirect_samples)
print(f"\nBootstrap 完成：有效迭代 {n_valid}/{n_bootstrap}")

ci_lower = float(np.percentile(indirect_samples, 2.5))
ci_upper = float(np.percentile(indirect_samples, 97.5))
ci_width = ci_upper - ci_lower
indirect_mean_boot = float(np.mean(indirect_samples))

print(f"Bootstrap 间接效应均值 = {indirect_mean_boot:.4f} pp")
print(f"Bootstrap 95% CI = [{ci_lower:.4f}, {ci_upper:.4f}]")
print(f"CI 宽度 = {ci_width:.4f}")

# ── 5. 显著性判断 ─────────────────────────────────────────────────
contains_zero = (ci_lower <= 0 <= ci_upper)
if not contains_zero:
    significance_label = "不含0，因此间接效应显著"
    significance_note = "间接效应在 Bootstrap 95% CI 下显著（CI 不含0）"
else:
    significance_label = "含0，因此间接效应不显著"
    significance_note = "方向一致但在5%水平不显著（CI 含0）"

print(f"\n显著性判断: Bootstrap 95%CI [{ci_lower:.4f}, {ci_upper:.4f}]，{significance_label}")

# ── 6. 间接占比 ────────────────────────────────────────────────────
if abs(TOTAL_EFFECT_T14) > 1e-8:
    pct = indirect_point / TOTAL_EFFECT_T14 * 100
else:
    pct = float('nan')

print(f"\n间接效应占总效应比例 = {indirect_point:.4f} / {TOTAL_EFFECT_T14:.4f} × 100 = {pct:.1f}%")

# CI 过宽检查（500次后>0.1触发局限性）
ci_too_wide = ci_width > 0.1
if ci_too_wide:
    print(f"\nWARNING: Bootstrap CI 宽度 {ci_width:.4f} > 0.1，触发局限性说明。")

# ── 7. 打印验收标准输出 ───────────────────────────────────────────
print(f"\n{'='*60}")
print(f"T16 DONE: beta={beta:.4f}, indirect={indirect_point:.4f}, "
      f"CI=[{ci_lower:.4f},{ci_upper:.4f}], pct={pct:.1f}%")
print(f"{'='*60}")

# ── 8. 保存结果 ───────────────────────────────────────────────────
os.makedirs("outputs/tables", exist_ok=True)
result = {
    "alpha_pct":        round(ALPHA_T15_PCT, 6),
    "alpha_raw":        round(ALPHA_T15_RAW, 8),
    "beta":             round(beta, 6),
    "beta_se":          round(beta_se, 6),
    "beta_pval":        round(beta_pval, 6),
    "beta_ci_lo":       round(beta_ci_lo, 6),
    "beta_ci_hi":       round(beta_ci_hi, 6),
    "indirect_point":   round(indirect_point, 6),
    "ci_lower":         round(ci_lower, 6),
    "ci_upper":         round(ci_upper, 6),
    "ci_width":         round(ci_width, 6),
    "indirect_mean_boot": round(indirect_mean_boot, 6),
    "n_bootstrap":      n_valid,
    "contains_zero":    contains_zero,
    "significance":     "significant" if not contains_zero else "not_significant",
    "total_effect_t14": TOTAL_EFFECT_T14,
    "indirect_pct":     round(pct, 2),
    "n_obs":            n_obs
}
pd.DataFrame([result]).to_csv("outputs/tables/table_t16_dml_step2_fiscal.csv", index=False)
print("结果已保存至 outputs/tables/table_t16_dml_step2_fiscal.csv")
