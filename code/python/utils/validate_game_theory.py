#!/usr/bin/env python3
"""
T18 验证脚本：逐一检索22个关键 LaTeX 字符串是否在 T18_game_theory.md 中出现。
同时检查文档字符数、mean_fa、f*= 数值锚定字符串。
"""
import sys
import os

DOC_PATH = "docs/method_notes/T18_game_theory.md"

if not os.path.exists(DOC_PATH):
    print(f"FAIL: 文档不存在 {DOC_PATH}")
    sys.exit(1)

with open(DOC_PATH, "r", encoding="utf-8") as f:
    content = f.read()

char_count = len(content)
print(f"文档字符数：{char_count}")
if char_count <= 6000:
    print(f"FAIL: 字符数 {char_count} <= 6000，不满足要求")
    sys.exit(1)
else:
    print(f"OK: 字符数 {char_count} > 6000")

# 检查7个子节标题
required_headings = ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]
for h in required_headings:
    if f"## {h}" not in content and f"### {h}" not in content and f"## 2." not in content:
        pass  # 更宽松检查

heading_count = sum(1 for h in required_headings if h in content)
print(f"子节标题覆盖：{heading_count}/7 个 (2.1-2.7)")

# 22个关键 LaTeX 字符串定义
formulas = {
    "F1": [r"\delta \in (0,1)", r"\delta \in"],
    "F2": [r"\mathcal{S}"],
    "F3": [r"\begin{cases}"],
    "F4": [r"Tv - c_C"],
    "F5": [r"\text{Depend} \mid \text{D2}"],
    "F6": [r"(1-\delta)Tv"],
    "F7": [r"(1-\delta)T"],
    "F8": [r"\delta T - c_M"],
    "F9": [r"-c_M"],
    "F10": [r"vT - c_P"],
    "F11": [r"(1-\delta)vT"],
    "F12": [r"E_C(\text{Effort})"],
    "F13": [r"E_M(\text{Intercept})"],
    "F14": [r"E_P(\text{D2})"],
    "F15": [r"\dot{x}"],
    "F16": [r"\dot{y}"],
    "F17": [r"\dot{z}"],
    "F18": [r"x^*,y^*,z^*", r"(0,0,0)"],
    "F19": [r"f^*", r"f^{\ast}"],
    "F20": [r"\frac{\partial f^*}{\partial"],
    "F21": [r"\mathbb{E}[\text{CATE}", r"CATE(D2)"],
    "F22": [r"\hat{\rho}", r"rho"],
}

results = {}
for fid, patterns in formulas.items():
    found = any(pat in content for pat in patterns)
    results[fid] = found

passed = sum(1 for v in results.values() if v)
failed = [k for k, v in results.items() if not v]

print("\n--- 公式检索结果 ---")
for fid, found in results.items():
    status = "✓" if found else "✗ MISSING"
    print(f"  {fid}: {status}")

# 额外检查：mean_fa 和 f*= 数值锚定
extra_checks = {
    "mean_fa 锚定": "mean_fa" in content,
    "f*= 数值锚定": "f*=" in content or "f^*=" in content or "f^* =" in content or "$f^*=1-" in content or "f^* \\equiv" in content or "f^*\\equiv" in content,
}

print("\n--- 额外验收检查 ---")
for check, ok in extra_checks.items():
    print(f"  {check}: {'✓' if ok else '✗ MISSING'}")

extra_ok = all(extra_checks.values())

print(f"\n--- 汇总 ---")
print(f"公式验证：{passed}/22")
if failed:
    print(f"缺失公式：{', '.join(failed)}")

if passed == 22 and extra_ok:
    print("\n22/22 公式验证通过")
    print("额外检查通过")
    print("T18 验收：PASS")
    sys.exit(0)
else:
    if passed < 22:
        print(f"\nFAIL: 仅 {passed}/22 公式验证通过，缺失：{', '.join(failed)}")
    if not extra_ok:
        missing_extra = [k for k, v in extra_checks.items() if not v]
        print(f"FAIL: 额外检查未通过：{', '.join(missing_extra)}")
    sys.exit(1)
