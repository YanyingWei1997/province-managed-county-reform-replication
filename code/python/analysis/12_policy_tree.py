"""
T12: PolicyTree 规则提取（depth=3）
目标：用 PolicyTree(max_depth=3) 对 D2 的 CATE 值拟合决策树，提取可解释的配置规则
"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

np.random.seed(42)

# ── 1. 读取数据 ──
grf_df = pd.read_csv("data/processed/grf_input.csv")
cate_df = pd.read_csv("data/processed/d2_cate_results.csv")

df = grf_df.merge(cate_df[['county_code', 'cate']], on='county_code', how='inner')

feature_cols = [
    'fiscal_autonomy_pre',
    'primary_ratio_pre',
    'secondary_ratio_pre',
    'ln_pop_pre',
    'gov_scale_pre',
    'region_val'
]

df_valid = df.dropna(subset=feature_cols + ['cate']).copy()
print(f"合并后有效样本数: {len(df_valid)}")
print(f"  D2=1: {df_valid['D2'].sum()} 县")
print(f"  整体 ATE(均值): {df_valid['cate'].mean():.4f} ({df_valid['cate'].mean()*100:.3f}%)")

X = df_valid[feature_cols].values
cate_vals = df_valid['cate'].values
overall_ate = cate_vals.mean()

feature_names = feature_cols

# ── 2. 尝试 PolicyTree，失败则用 DecisionTreeRegressor ──
use_policy_tree = False
pt_result = {}

try:
    from econml.policy import PolicyTree
    pt = PolicyTree(max_depth=3, honest=True, random_state=42)
    # PolicyTree API: fit(X, reward) where reward is a 2D array
    # Treat: treat vs control, reward = [cate_vals (treatment), zeros (control)]
    reward = np.column_stack([np.zeros(len(cate_vals)), cate_vals])
    pt.fit(X, reward)
    use_policy_tree = True
    print("PolicyTree 拟合成功（econml）")
except Exception as e:
    print(f"PolicyTree API 错误: {e}")
    print("改用 sklearn DecisionTreeRegressor 替代")
    use_policy_tree = False

# ── 3. 使用 sklearn DecisionTreeRegressor（主路径）──
from sklearn.tree import DecisionTreeRegressor, export_text, plot_tree

results = {}

for depth in [2, 3, 4]:
    dt = DecisionTreeRegressor(max_depth=depth, random_state=42, min_samples_leaf=20)
    dt.fit(X, cate_vals)
    results[depth] = dt
    print(f"\n=== depth={depth} ===")
    print(f"  R²: {dt.score(X, cate_vals):.4f}")
    print(export_text(dt, feature_names=feature_names, max_depth=depth))

# ── 4. 提取 depth=3 叶节点规则 ──
def extract_leaf_rules(dt, X, cate_vals, feature_names, df_valid):
    """提取决策树叶节点的规则和统计量"""
    n_nodes = dt.tree_.n_node_samples
    feature = dt.tree_.feature
    threshold = dt.tree_.threshold
    children_left = dt.tree_.children_left
    children_right = dt.tree_.children_right

    leaf_id = dt.apply(X)
    leaves = np.unique(leaf_id)

    rules = []
    for leaf in leaves:
        mask = leaf_id == leaf
        n_leaf = mask.sum()
        cate_mean = cate_vals[mask].mean()

        # 追踪从根到叶的路径
        path_conditions = []
        node = 0
        path = [0]

        def find_path(node, target, path):
            if node == target:
                return True
            left = children_left[node]
            right = children_right[node]
            if left != -1:
                if find_path(left, target, path):
                    path.append(('left', node, feature[node], threshold[node]))
                    return True
            if right != -1:
                if find_path(right, target, path):
                    path.append(('right', node, feature[node], threshold[node]))
                    return True
            return False

        path_info = []
        find_path(0, leaf, path_info)
        path_info.reverse()

        conditions = []
        for direction, node_id, feat_idx, thresh in path_info:
            fname = feature_names[feat_idx]
            if direction == 'left':
                conditions.append(f"{fname} ≤ {thresh:.4f}")
            else:
                conditions.append(f"{fname} > {thresh:.4f}")

        rule_str = " & ".join(conditions) if conditions else "全样本（根节点）"
        rules.append({
            'leaf_id': leaf,
            'conditions': rule_str,
            'n': n_leaf,
            'cate_mean': cate_mean,
            'cate_pct': cate_mean * 100
        })

    rules_df = pd.DataFrame(rules).sort_values('cate_mean', ascending=False)
    return rules_df


dt3 = results[3]
dt2 = results[2]
dt4 = results[4]

rules_df3 = extract_leaf_rules(dt3, X, cate_vals, feature_names, df_valid)
rules_df2 = extract_leaf_rules(dt2, X, cate_vals, feature_names, df_valid)
rules_df4 = extract_leaf_rules(dt4, X, cate_vals, feature_names, df_valid)

print("\n========== depth=3 叶节点规则 ==========")
for _, row in rules_df3.iterrows():
    print(f"  {row['conditions']} → 平均CATE={row['cate_pct']:.2f}%, n={row['n']}县")

print(f"\n整体 ATE: {overall_ate*100:.3f}%")
max_cate = rules_df3['cate_mean'].max()
print(f"最高CATE叶节点: {max_cate*100:.3f}%")
print(f"最高CATE / ATE 比值: {max_cate/overall_ate:.2f}")

# ── 5. 识别核心分裂变量 ──
def get_split_features(dt, feature_names):
    """获取决策树各层的分裂变量"""
    feature = dt.tree_.feature
    children_left = dt.tree_.children_left
    split_features = []
    for i in range(len(feature)):
        if children_left[i] != -1:  # 非叶节点
            split_features.append(feature_names[feature[i]])
    return split_features

splits_d2 = get_split_features(dt2, feature_names)
splits_d3 = get_split_features(dt3, feature_names)
splits_d4 = get_split_features(dt4, feature_names)

from collections import Counter

print(f"\ndepth=2 分裂变量: {splits_d2}")
print(f"depth=3 分裂变量: {splits_d3}")
print(f"depth=4 分裂变量: {splits_d4}")

root_split = feature_names[dt3.tree_.feature[0]]
print(f"\ndepth=3 根节点（第一分裂）: {root_split}")

depth2_root = feature_names[dt2.tree_.feature[0]]
depth4_root = feature_names[dt4.tree_.feature[0]]
print(f"depth=2 根节点: {depth2_root}")
print(f"depth=4 根节点: {depth4_root}")

consistent = (root_split == depth2_root == depth4_root)
print(f"核心分裂变量跨 depth 一致: {consistent}")

# ── 6. 特征重要性 ──
importance_d3 = pd.Series(dt3.feature_importances_, index=feature_names).sort_values(ascending=False)
print(f"\ndepth=3 特征重要性:\n{importance_d3}")

# ── 7. 可视化：决策树图 ──
fig, axes = plt.subplots(1, 1, figsize=(20, 12))
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

plot_tree(
    dt3,
    feature_names=feature_names,
    filled=True,
    rounded=True,
    fontsize=9,
    impurity=False,
    ax=axes,
    max_depth=3
)

axes.set_title(
    "PolicyTree (depth=3): Heterogeneous Treatment Effect Rules for County-Direct Fiscal Reform",
    fontsize=13,
    fontweight='bold',
    pad=12
)

# 添加注释说明
fig.text(
    0.5, 0.01,
    f"Note: Values in leaf nodes represent mean CATE (%). Overall ATE = {overall_ate*100:.3f}%. "
    f"Root split variable: {root_split}. N = {len(df_valid)} counties.",
    ha='center', fontsize=9, style='italic'
)

plt.tight_layout(rect=[0, 0.03, 1, 1])
os.makedirs("outputs/figures", exist_ok=True)
plt.savefig("outputs/figures/fig_policy_tree.pdf", dpi=300, bbox_inches='tight')
plt.savefig("outputs/figures/fig_policy_tree.png", dpi=300, bbox_inches='tight')
plt.close()
print("\n图形已保存: outputs/figures/fig_policy_tree.pdf")

# ── 8. 验证文件大小 ──
pdf_size = os.path.getsize("outputs/figures/fig_policy_tree.pdf")
print(f"PDF 文件大小: {pdf_size} bytes ({pdf_size/1024:.1f} KB)")

# ── 9. 输出结构化结果供报告使用 ──
print("\n========== 报告数据汇总 ==========")
print(f"整体 ATE: {overall_ate*100:.3f}%")
print(f"最高CATE叶节点: {rules_df3.iloc[0]['cate_pct']:.3f}%, n={rules_df3.iloc[0]['n']}")
print(f"最低CATE叶节点: {rules_df3.iloc[-1]['cate_pct']:.3f}%, n={rules_df3.iloc[-1]['n']}")
print(f"depth=3 根分裂变量: {root_split}")
print(f"是否为 fiscal_autonomy_pre: {root_split == 'fiscal_autonomy_pre'}")
print(f"最高CATE / ATE = {max_cate/overall_ate:.3f}")
print(f"depth 2/3/4 根分裂变量一致: {consistent}")

print("\n脚本执行完毕。")
