"""第3章案例：读懂一张成绩回归表。

生成正文图3-3（回归表中各系数的点估计与95%置信区间）。

数据与第2章完全同源：同一份数据生成过程、同一个随机种子，因此两章的数字可以直接
对照。第2章关心"AI 系数等于多少"，本章关心"这个数字有多确定"。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

SEED = 20260914
N = 800
TRUE_BETA_AI = 1.25

HERE = Path(__file__).resolve().parent
IMAGE_DIR = Path(__file__).resolve().parents[3] / "图片" / "教材插图"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)

ability = rng.normal(0, 1, size=N)
age = np.clip(np.round(rng.normal(20, 1.6, size=N)), 17, 26)
female = rng.integers(0, 2, size=N)

ai = 8 + 3.2 * ability + 0.25 * (age - 20) - 1.2 * female + rng.normal(0, 3.5, size=N)
ai = np.clip(ai, 0, 30)
score = (
    68
    + TRUE_BETA_AI * ai
    + 4.5 * ability
    + 0.6 * (age - 20)
    - 1.8 * female
    + rng.normal(0, 5.5, size=N)
)

df = pd.DataFrame(
    {"score": score, "ai": ai, "age": age, "female": female, "ability": ability}
)

xs = ["ai", "age", "female", "ability"]
model = sm.OLS(df["score"], sm.add_constant(df[xs])).fit()
ci = model.conf_int(alpha=0.05)

table = pd.DataFrame(
    {
        "coef": model.params,
        "std_err": model.bse,
        "t_value": model.tvalues,
        "p_value": model.pvalues,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
    }
)
table.to_csv(HERE / "ch03_regression_table.csv", encoding="utf-8-sig")

# 联合检验：年龄与性别能否同时排除
joint_test = model.f_test("age = 0, female = 0")

print("回归表（被解释变量：课程成绩）：")
print(table.round(5).to_string())
print(f"\n样本量：{int(model.nobs)}，R² = {model.rsquared:.4f}，"
      f"调整R² = {model.rsquared_adj:.4f}")
print(f"整体F统计量：{model.fvalue:.3f}，p = {model.f_pvalue:.4g}")
print("\n联合检验 H0: age = female = 0")
print(joint_test)
print(f"\nAI 系数的手工t值：{model.params['ai'] / model.bse['ai']:.5f}")

# 图3-3：各系数的点估计与置信区间（截距不绘制）
plot_vars = ["ai", "age", "female", "ability"]
labels = ["AI 使用时间", "年龄", "性别（女性=1）", "认知能力"]
sub = table.loc[plot_vars]
y = np.arange(len(plot_vars))

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8.6, 4.8))
ax.errorbar(
    sub["coef"],
    y,
    xerr=[sub["coef"] - sub["ci_lower"], sub["ci_upper"] - sub["coef"]],
    fmt="o",
    color="#2A6F97",
    ecolor="#6C8EAD",
    capsize=4,
    markersize=7,
)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_yticks(y, labels)
ax.invert_yaxis()
ax.set_xlabel("回归系数及 95% 置信区间")
ax.set_title("成绩回归表：点估计与不确定性")
fig.tight_layout()
output = IMAGE_DIR / "ch03-fig3-regression-table-and-ci.png"
fig.savefig(output, dpi=220, bbox_inches="tight")
print(f"\n图形已保存：{output}")
