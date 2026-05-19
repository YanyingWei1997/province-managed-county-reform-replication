"""
T17: DML 中介路径2 - 财政支出中介效应（γ×δ）
Step1: D2 → ln_fiscal_exp_pc 的效应 γ（LinearDML）
Step2: ln_fiscal_exp_pc → gdp_growth_pc 的效应 δ（控制 D2）
Bootstrap: 200次重采样
与 T15-T16（fiscal_autonomy 路径）完全平行的逻辑，中介变量改为 ln_fiscal_exp_pc
"""
import numpy as np
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LassoCV
import os
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ── 0. 常量（来自 T14 总处理效应）──────────────────────────────────
TOTAL_EFFECT_T14 = 1.0415  # T14 DML theta，单位：pp

# T15/T16 路径1结果（用于对比表）
ALPHA_T15 = -1.4252   # D2→fiscal_autonomy（百分点）
BETA_T16  =  2.0538   # fiscal_autonomy→gdp（pp/unit）
INDIRECT1 = -0.0293   # α×β（pp）
CI1_LO    = -0.0569
CI1_HI    =  0.0004
PCT1      = -2.8

# ── 1. 读取数据 ──────────────────────────────────────────────────
df_raw = pd.read_csv("data/processed/dml_panel_within.csv")

# 先删除 ln_fiscal_exp_pc_w 缺失行（须在报告中注明有效样本量）
cols_need = ["gdp_growth_pc_w", "ln_fiscal_exp_pc_w", "D2_w",
             "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
df = df_raw.dropna(subset=cols_need).copy()

n_total_raw = len(df_raw)
n_valid = len(df)
missing_rate = (n_total_raw - n_valid) / n_total_raw
nonmissing_rate = n_valid / n_total_raw

print(f"原始样本量: {n_total_raw}")
print(f"有效样本量（删除 ln_fiscal_exp_pc_w 缺失行后）: {n_valid}")
print(f"非空率: {nonmissing_rate:.4f} ({nonmissing_rate*100:.1f}%)")

if nonmissing_rate < 0.40:
    sample_note = "WARNING: 样本量不足（非空率<40%），结果仅供参考"
    print(sample_note)
else:
    sample_note = f"有效样本量充足（非空率={nonmissing_rate*100:.1f}%）"
    print(sample_note)

# ── 2. Step1: 估计 γ（D2 → ln_fiscal_exp_pc）───────────────────
# Y1 = ln_fiscal_exp_pc_w
# T1 = D2_w
# W1 = [primary_ratio_w, secondary_ratio_w, ln_pop_w, gov_scale_w]（同T15）
Y1 = df["ln_fiscal_exp_pc_w"].values
T1 = df["D2_w"].values
W1 = df[["primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values

print(f"\nY1 (ln_fiscal_exp_pc_w) 均值: {Y1.mean():.6e}  std: {Y1.std():.4f}")
print(f"T1 (D2_w) 均值: {T1.mean():.6e}  std: {T1.std():.4f}")

model_step1 = LinearDML(
    model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
    model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
    random_state=42
)
model_step1.fit(Y1, T1, X=None, W=W1)

inf1 = model_step1.intercept__inference()
gamma = float(np.atleast_1d(inf1.point_estimate).ravel()[0])
gamma_se = float(np.atleast_1d(inf1.pred_stderr).ravel()[0])
gamma_pval = float(np.atleast_1d(inf1.pvalue()).ravel()[0])
gamma_ci = inf1.conf_int()
gamma_ci_lo = float(np.atleast_1d(gamma_ci[0]).ravel()[0])
gamma_ci_hi = float(np.atleast_1d(gamma_ci[1]).ravel()[0])

print(f"\n{'='*60}")
print(f"T17 Step1 结果：γ（D2 → ln_fiscal_exp_pc）")
print(f"{'='*60}")
print(f"γ = {gamma:.6f} (对数单位)")
print(f"SE = {gamma_se:.6f}")
print(f"p值 = {gamma_pval:.4f}")
print(f"95% CI: [{gamma_ci_lo:.6f}, {gamma_ci_hi:.6f}]")

# ── 3. Step2: 估计 δ（ln_fiscal_exp_pc → gdp_growth_pc，控制 D2）─
# Y2 = gdp_growth_pc_w（百分点）
# T2 = ln_fiscal_exp_pc_w（对数单位）
# W2 = [D2_w, primary_ratio_w, secondary_ratio_w, ln_pop_w, gov_scale_w]（同T16）
Y2 = df["gdp_growth_pc_w"].values
T2 = df["ln_fiscal_exp_pc_w"].values
W2 = df[["D2_w", "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values

print(f"\nY2 (gdp_growth_pc_w) 均值: {Y2.mean():.6e}  std: {Y2.std():.4f}")
print(f"T2 (ln_fiscal_exp_pc_w) 均值: {T2.mean():.6e}  std: {T2.std():.4f}")

model_step2 = LinearDML(
    model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
    model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
    random_state=42
)
model_step2.fit(Y2, T2, X=None, W=W2)

inf2 = model_step2.intercept__inference()
delta = float(np.atleast_1d(inf2.point_estimate).ravel()[0])
delta_se = float(np.atleast_1d(inf2.pred_stderr).ravel()[0])
delta_pval = float(np.atleast_1d(inf2.pvalue()).ravel()[0])
delta_ci = inf2.conf_int()
delta_ci_lo = float(np.atleast_1d(delta_ci[0]).ravel()[0])
delta_ci_hi = float(np.atleast_1d(delta_ci[1]).ravel()[0])

print(f"\n{'='*60}")
print(f"T17 Step2 结果：δ（ln_fiscal_exp_pc → gdp_growth_pc）")
print(f"{'='*60}")
print(f"δ = {delta:.6f} pp/单位对数")
print(f"SE = {delta_se:.6f}")
print(f"p值 = {delta_pval:.4f}")
print(f"95% CI: [{delta_ci_lo:.6f}, {delta_ci_hi:.6f}]")

# ── 4. 点估计间接效应 ─────────────────────────────────────────────
# γ 单位：ln_fiscal_exp_pc 变化量（对数单位）
# δ 单位：pp gdp_growth_pc / 单位 ln_fiscal_exp_pc（对数）
# 间接效应 = γ × δ（单位：pp gdp_growth_pc）
indirect2_point = gamma * delta
print(f"\n间接效应（点估计）= γ × δ = {gamma:.6f} × {delta:.6f} = {indirect2_point:.6f} pp")

# ── 5. Bootstrap 间接效应（200次）────────────────────────────────

def fit_step1_boot(df_b):
    """Bootstrap Step1: D2 → ln_fiscal_exp_pc"""
    cols = ["ln_fiscal_exp_pc_w", "D2_w", "primary_ratio_w",
            "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
    db = df_b.dropna(subset=cols)
    Y_b = db["ln_fiscal_exp_pc_w"].values
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
    """Bootstrap Step2: ln_fiscal_exp_pc → gdp_growth_pc（控制 D2）"""
    cols = ["gdp_growth_pc_w", "ln_fiscal_exp_pc_w", "D2_w",
            "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
    db = df_b.dropna(subset=cols)
    Y_b = db["gdp_growth_pc_w"].values
    T_b = db["ln_fiscal_exp_pc_w"].values
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
print(f"{'='*60}")

n_bootstrap = 200
indirect_samples = []
n_obs = len(df)
rng = np.random.default_rng(42)

for i in range(n_bootstrap):
    idx = rng.choice(n_obs, n_obs, replace=True)
    df_boot = df.iloc[idx].copy()
    try:
        gamma_b = fit_step1_boot(df_boot)
        delta_b = fit_step2_boot(df_boot)
        indirect_b = gamma_b * delta_b
        indirect_samples.append(indirect_b)
    except Exception:
        pass
    if (i + 1) % 20 == 0:
        print(f"  Bootstrap 进度: {i+1}/{n_bootstrap}")

indirect_samples = np.array(indirect_samples)
n_valid_boot = len(indirect_samples)
print(f"\nBootstrap 完成：有效迭代 {n_valid_boot}/{n_bootstrap}")

ci2_lower = float(np.percentile(indirect_samples, 2.5))
ci2_upper = float(np.percentile(indirect_samples, 97.5))
ci2_width = ci2_upper - ci2_lower
indirect2_mean_boot = float(np.mean(indirect_samples))

print(f"Bootstrap 间接效应均值 = {indirect2_mean_boot:.6f} pp")
print(f"Bootstrap 95% CI = [{ci2_lower:.4f}, {ci2_upper:.4f}]")
print(f"CI 宽度 = {ci2_width:.4f}")

# ── 6. 显著性判断 ─────────────────────────────────────────────────
contains_zero2 = (ci2_lower <= 0 <= ci2_upper)
if not contains_zero2:
    sig2_label = "不含0，间接效应显著"
    sig2_yn = "是"
else:
    sig2_label = "含0，间接效应不显著"
    sig2_yn = "否"

print(f"\n显著性判断: Bootstrap 95%CI [{ci2_lower:.4f}, {ci2_upper:.4f}]，{sig2_label}")

# ── 7. 间接占比 ────────────────────────────────────────────────────
if abs(TOTAL_EFFECT_T14) > 1e-8:
    pct2 = indirect2_point / TOTAL_EFFECT_T14 * 100
else:
    pct2 = float('nan')

print(f"\n间接效应占总效应比例 = {indirect2_point:.6f} / {TOTAL_EFFECT_T14:.4f} × 100 = {pct2:.1f}%")

# ── 8. 路径1显著性标签（用于对比表）─────────────────────────────
sig1_yn = "否"  # T16 Bootstrap CI = [-0.0569, 0.0004] 含0

# ── 9. 打印对比表 ─────────────────────────────────────────────────
print(f"\n{'='*70}")
print("双路径中介效应对比表")
print(f"{'='*70}")
print(f"{'路径':<30}{'γ/α':<12}{'δ/β':<12}{'间接效应':<12}{'Bootstrap CI':<22}{'占比':<10}{'显著'}")
print(f"{'-'*70}")
print(f"D2→fiscal_autonomy→gdp  {ALPHA_T15:<12.4f}{BETA_T16:<12.4f}{INDIRECT1:<12.4f}[{CI1_LO:.4f},{CI1_HI:.4f}]  {PCT1:<10.1f}{sig1_yn}")
print(f"D2→ln_fiscal_exp→gdp    {gamma:<12.6f}{delta:<12.6f}{indirect2_point:<12.6f}[{ci2_lower:.4f},{ci2_upper:.4f}]  {pct2:<10.1f}{sig2_yn}")
print(f"{'='*70}")

# ── 10. 打印验收标准输出 ──────────────────────────────────────────
print(f"\n{'='*60}")
print(f"T17 DONE: gamma={gamma:.6f}, delta={delta:.6f}, indirect2={indirect2_point:.6f}, "
      f"CI=[{ci2_lower:.4f},{ci2_upper:.4f}], pct={pct2:.1f}%")
print(f"{'='*60}")

# ── 11. 保存结果 ──────────────────────────────────────────────────
os.makedirs("outputs/tables", exist_ok=True)
result = {
    "gamma":              round(gamma, 8),
    "gamma_se":           round(gamma_se, 8),
    "gamma_pval":         round(gamma_pval, 6),
    "gamma_ci_lo":        round(gamma_ci_lo, 8),
    "gamma_ci_hi":        round(gamma_ci_hi, 8),
    "delta":              round(delta, 8),
    "delta_se":           round(delta_se, 8),
    "delta_pval":         round(delta_pval, 6),
    "delta_ci_lo":        round(delta_ci_lo, 8),
    "delta_ci_hi":        round(delta_ci_hi, 8),
    "indirect2_point":    round(indirect2_point, 8),
    "ci2_lower":          round(ci2_lower, 6),
    "ci2_upper":          round(ci2_upper, 6),
    "ci2_width":          round(ci2_width, 6),
    "indirect2_mean_boot":round(indirect2_mean_boot, 8),
    "n_bootstrap":        n_valid_boot,
    "contains_zero":      contains_zero2,
    "significance":       "significant" if not contains_zero2 else "not_significant",
    "total_effect_t14":   TOTAL_EFFECT_T14,
    "indirect_pct":       round(pct2, 4),
    "n_obs":              n_obs,
    "nonmissing_rate":    round(nonmissing_rate, 6),
    "sample_note":        sample_note,
}
pd.DataFrame([result]).to_csv("outputs/tables/table_t17_dml_exp.csv", index=False)
print("结果已保存至 outputs/tables/table_t17_dml_exp.csv")
