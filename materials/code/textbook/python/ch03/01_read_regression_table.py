"""第3章案例：读懂一张工资回归表。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

SEED = 20260910
HERE = Path(__file__).resolve().parent
IMAGE_DIR = Path(__file__).resolve().parents[3] / "图片"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)

# 与第2章口径一致的教学工资数据；本脚本可独立运行。
n = 800
background = rng.normal(size=n)
educ = 14 + 1.1 * background + rng.normal(0, 1.2, size=n)
exper = 12 + 1.8 * background + rng.normal(0, 3.0, size=n)
tenure = 4 + 0.25 * exper + 0.5 * background + rng.normal(0, 1.8, size=n)
u = rng.normal(0, 0.25, size=n)
ln_wage = 1.6 + 0.08 * educ + 0.035 * exper + 0.02 * tenure + u
df = pd.DataFrame({"ln_wage": ln_wage, "educ": educ, "exper": exper, "tenure": tenure})

model = sm.OLS(df["ln_wage"], sm.add_constant(df[["educ", "exper", "tenure"]])).fit()
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

# 联合检验：经验和任职年限能否同时排除
joint_test = model.f_test("exper = 0, tenure = 0")

print(model.summary())
print("\n整理后的回归表：")
print(table.round(5))
print("\n联合检验 H0: exper = tenure = 0")
print(joint_test)
print(f"\n教育系数的手工t值：{model.params['educ'] / model.bse['educ']:.5f}")

# 系数及95%置信区间图（截距不绘制）
plot_vars = ["educ", "exper", "tenure"]
labels = ["教育年限", "工作经验", "任职年限"]
sub = table.loc[plot_vars]
y = np.arange(len(plot_vars))

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.errorbar(
    sub["coef"],
    y,
    xerr=[sub["coef"] - sub["ci_lower"], sub["ci_upper"] - sub["coef"]],
    fmt="o",
    color="#2A6F97",
    ecolor="#6C8EAD",
    capsize=4,
)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_yticks(y, labels)
ax.invert_yaxis()
ax.set_xlabel("回归系数及95%置信区间")
ax.set_title("工资回归表：点估计与不确定性")
fig.tight_layout()
output = IMAGE_DIR / "ch03-fig3-regression-table-and-ci.png"
fig.savefig(output, dpi=220, bbox_inches="tight")
print(f"\n图形已保存：{output}")
