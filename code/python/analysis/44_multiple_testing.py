"""
Apply Bonferroni and Holm-Bonferroni multiple-testing corrections to the
family of heterogeneity tests in §4.4.

Tests in the family:
1. Pearson r(CATE, fa_pre)
2. Welch t-test on CATE median split
3. Single-variable causal-forest r
4. ANOVA F across regions
5. Subgroup TWFE Q4 (only Q4 is marginally significant; others n.s.)
6. Interaction TWFE D2 × Q1
7. Heterogeneity test (interaction TWFE D2×Q1 = D2×Q4)
"""
import pandas as pd

# Heterogeneity-test family p-values (from project outputs)
tests = [
    ("Pearson r(CATE, fa_pre)",                       0.000012),
    ("Welch t-test on CATE median split",             0.000204),
    ("Single-variable causal-forest r",               1e-6),    # reported as <1e-6
    ("ANOVA F across regions",                        0.001),
    ("Subgroup TWFE Q4",                              0.078),
    ("Interaction TWFE D2 x Q1",                      0.0005),
    ("Heterogeneity F-test (D2xQ1 = D2xQ4)",          0.0001),
]
m = len(tests)
df = pd.DataFrame(tests, columns=["test", "p_raw"])
df = df.sort_values("p_raw").reset_index(drop=True)
df["rank"] = df.index + 1

# Bonferroni
df["p_bonferroni"] = (df["p_raw"] * m).clip(upper=1)

# Holm-Bonferroni
holm = []
for i in range(m):
    pi = df.loc[i, "p_raw"]
    h = pi * (m - i)
    holm.append(min(h, 1))
# enforce monotone non-decreasing
for i in range(1, m):
    holm[i] = max(holm[i], holm[i-1])
df["p_holm"] = holm

# Significance tags
def stars(p):
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

for col in ["p_raw", "p_bonferroni", "p_holm"]:
    df[col + "_sig"] = df[col].apply(stars)

print(f"Multiple testing correction: m = {m} tests in heterogeneity family")
print()
print(df.to_string(index=False))

# Save table
out_csv = "./outputs/tables/table_multiple_testing.csv"
df.to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")

# Summary
print("\n=== Summary ===")
n_raw_sig05 = (df["p_raw"] < 0.05).sum()
n_bonf_sig05 = (df["p_bonferroni"] < 0.05).sum()
n_holm_sig05 = (df["p_holm"] < 0.05).sum()
print(f"Tests significant at 5% (raw):       {n_raw_sig05}/{m}")
print(f"Tests significant at 5% (Bonferroni): {n_bonf_sig05}/{m}")
print(f"Tests significant at 5% (Holm):       {n_holm_sig05}/{m}")
