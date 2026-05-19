# Figure Captions / 图注参考

---

## Figure 1 — Causal Identification

**English:**
Dynamic treatment effects and cross-estimator comparison for the county-direct fiscal reform (D2). Panel (a) plots event-study coefficients from three estimators—TWFE (solid line), Sun & Abraham (2021) (dashed), and Gardner (2021) (dotted)—with 95% confidence intervals. Shaded bands denote three functional windows: pre-trend window (t=−5 to t=−2, light gray), anticipation window (t=−1, orange), and post-reform window (t≥0, white). The pre-trend joint F-test (t=−5 to t=−2) yields p=0.51 for TWFE, p>0.28 for Sun–Abraham, and p=0.33 for Gardner. The significant negative coefficient at t=−1 (ATT ≈ −1.0 pp) is interpreted as Ashenfelter's dip, reflecting officials' anticipatory behavioral adjustment ahead of the reform. Panel (b) compares the average post-reform ATT across the three estimators. ** p < 0.01.

**中文：**
省管县财政改革（D2）的动态处理效应与多估计量比较。面板(a)为三种估计量（TWFE 实线、Sun-Abraham 2021 虚线、Gardner 2021 点线）的事件研究系数及95%置信区间，浅灰、橙色、白色三个功能区分别标注预趋势窗口（t=−5至t=−2）、预期效应窗口（t=−1）和改革后窗口（t≥0）。预趋势联合F检验（t=−5至t=−2）：TWFE p=0.51，Sun-Abraham p>0.28，Gardner p=0.33，均通过。t=−1期显著负系数（ATT≈−1.0 pp）被解读为Ashenfelter's dip，反映官员对即将到来改革的预期调整行为。面板(b)比较三种估计量的改革后平均ATT。** p<0.01。

---

## Figure 2 — Heterogeneity (Constraint Line Analysis)

**English:**
Constraint line analysis of county-level heterogeneous treatment effects (CATE) with respect to six pre-reform county characteristics. Each panel plots the 95th-percentile upper boundary (red) and 5th-percentile lower boundary (blue) of CATE within bins of the x-variable, fitted with an automatically selected polynomial (degree 2 or 3 by adjusted R²). Shaded bands indicate 95% bootstrap confidence intervals (200 replications). Hollow circles mark boundary extreme points. Background scatter shows county-level observations (clipped at 2nd–98th percentile of x).

**中文：**
基于六个改革前县域特征的CATE约束线分析。每幅子图绘制x变量分组内CATE的第95百分位上边界（红色）与第5百分位下边界（蓝色），采用自动选择的多项式拟合（根据校正R²在2次和3次中取优）。阴影带为200次Bootstrap自举95%置信区间，空心圆标注边界极值点，背景散点为县级观测值（x方向裁剪至2%—98%分位）。

---

## Figure 3 — Regional Heterogeneity Drivers

**English:**
Panel (a) presents standardized OLS coefficients in heatmap form, estimated separately for eastern (n=278), central (n=504), and western (n=479) regions. Panel (b) shows the same coefficients with 95% confidence intervals in grouped bar chart form for direct comparison across regions. All variables are standardized (mean zero, unit variance) prior to estimation. Values marked with * indicate statistical significance at the 5% level. Colors: blue = positive coefficient, red = negative coefficient. The legend shows region color coding.

**中文：**
面板(a)以热力图形式展示分别在东部（n=278）、中部（n=504）、西部（n=479）样本中估计的标准化OLS系数。面板(b)以分组条形图形式展示相同系数及95%置信区间，便于区域间直接比较。所有变量在估计前均经过标准化处理（均值为零，方差为1）。带*数值表示在5%水平上统计显著。蓝色=正系数，红色=负系数。图例标注区域颜色编码。

---

## Figure 4 — Spatial Distribution of CATE and Pre-Reform Fiscal Autonomy

**English:**
Spatial distribution of GRF-estimated CATE and pre-reform fiscal autonomy across the 1,242 counties in the analytical sample with successful coordinate matching (out of 1,261 GRF cross-sectional observations; 19 unmatched due to administrative renaming/merging). Marker color encodes the GRF CATE on a five-segment red-to-blue diverging scale with bin boundaries at −7, −3.5, −2.0, −0.5, +0.5, +2 percentage points (red = more negative cross-sectional CATE, blue = less negative or near-positive). Marker size encodes pre-reform fiscal autonomy `fiscal_autonomy_pre` (larger marker = higher autonomy; clipped at the 2nd–98th percentile range for visual readability). Solid markers indicate D2-treated counties (n=562); hollow markers with black edges indicate never-treated counties (n=680). Gold five-pointed stars mark the 35 counties belonging to the PolicyTree highest-CATE leaf, defined by `secondary_ratio_pre` ≤ 18.86% and `fiscal_autonomy_pre` ≤ 0.049 (mean leaf CATE ≈ +0.45 pp), the only PolicyTree leaf with a non-negative CATE point estimate. Light grey lines show provincial administrative boundaries (DataV.Aliyun 2023). Per the T06A identification diagnostic (PS AUC = 0.692, max|SMD| = 0.556, pre-outcome placebo p = 0.0001), all CATE values are interpreted as **Exploratory Only**: the spatial pattern shown here describes how cross-sectional level differences vary across counties as a function of pre-reform observables, not a causal estimate of treatment-effect heterogeneity. The geographic concentration of gold stars in the southwestern and inland-mountainous belt (Yunnan-Guizhou plateau, southern Sichuan, parts of Guangxi and western Hunan) corresponds to the $f \ll f^*$ regime predicted by Proposition 1 of the evolutionary game model.

**中文：**
GRF 估计的 CATE 与改革前财政自主度在分析样本 1,242 个成功匹配坐标县（1,261 个 GRF 截面观测中，19 个因行政区划更名/合并未成功匹配）的空间分布。点的颜色按红蓝五段发散色阶编码 GRF CATE，分箱边界为 −7、−3.5、−2.0、−0.5、+0.5、+2 个百分点（红色 = 截面 CATE 更负，蓝色 = 更不那么负或接近正）。点的大小编码改革前财政自主度 `fiscal_autonomy_pre`（点越大 = 自主度越高；为视觉可读性已裁剪至第 2–98 百分位区间）。实心点为 D2 处理县（n=562），带黑色边线的空心点为从未处理县（n=680）。金色五角星标记 35 个属于 PolicyTree 最高 CATE 叶节点的县，叶节点定义为 `secondary_ratio_pre` ≤ 18.86% 且 `fiscal_autonomy_pre` ≤ 0.049（叶节点均值 CATE ≈ +0.45 pp），是 PolicyTree 中唯一 CATE 点估计非负的叶。浅灰线为省级行政边界（DataV.Aliyun 2023）。根据 T06A 识别诊断（PS AUC = 0.692，max|SMD| = 0.556，改革前结果安慰剂 p = 0.0001），所有 CATE 值解读为**仅探索性**：本图所示空间模式描述各县截面层面水平差异如何随改革前可观测变量变化，并非处理效应异质性的因果估计。金色星标在西南与内陆山区带（云贵高原、川南、广西与湘西部分）的地理聚集，对应演化博弈模型 Proposition 1 所预测的 $f \ll f^*$ 区域。

---

*生成时间：2026-04-27*
*对应脚本：scripts/visualization/22_final_figures.py（Fig 1–3）；scripts/visualization/40_spatial_cate_map.py（Fig 4）*
