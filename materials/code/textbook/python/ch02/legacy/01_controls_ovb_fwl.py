"""备选案例：教育、经验与工资——控制变量、遗漏变量与FWL。

用 FWL 定理演示遗漏变量偏误。生成一张图和一份模型比较表，
全部保存到本脚本同级的 output/ 文件夹。
"""

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

SEED = 20260910
HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
# 输出目录：默认写到本脚本同级的 output/，下载到任何位置都能直接运行，不依赖仓库结构。
# 需要把生成的图汇入教材插图库时，运行时指定：
#   CASE_OUTPUT_DIR=<仓库>/30_教学/09_计量教材/图片/教材插图 python 01_controls_ovb_fwl.py
OUTPUT_DIR = Path(os.environ.get("CASE_OUTPUT_DIR", HERE / "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)

# 教学用工资数据：完整模型满足零条件均值与同方差。
n = 800
background = rng.normal(size=n)
educ = 14 + 1.1 * background + rng.normal(0, 1.2, size=n)
exper = 12 + 1.8 * background + rng.normal(0, 3.0, size=n)
tenure = 4 + 0.25 * exper + 0.5 * background + rng.normal(0, 1.8, size=n)
u = rng.normal(0, 0.25, size=n)
ln_wage = 1.6 + 0.08 * educ + 0.035 * exper + 0.02 * tenure + u

df = pd.DataFrame({"ln_wage": ln_wage, "educ": educ, "exper": exper, "tenure": tenure})

# 任务1：遗漏模型与完整模型
omit = sm.OLS(df["ln_wage"], sm.add_constant(df[["educ"]])).fit()
full = sm.OLS(df["ln_wage"], sm.add_constant(df[["educ", "exper", "tenure"]])).fit()
comparison = pd.DataFrame(
    {
        "model": ["只含教育", "控制经验与任职年限"],
        "educ_coef": [omit.params["educ"], full.params["educ"]],
        "educ_se": [omit.bse["educ"], full.bse["educ"]],
        "r_squared": [omit.rsquared, full.rsquared],
    }
)
comparison.to_csv(OUTPUT_DIR / "ch02_model_comparison.csv", index=False, encoding="utf-8-sig")

# 任务2和3：FWL三步法
controls = sm.add_constant(df[["exper", "tenure"]])
educ_aux = sm.OLS(df["educ"], controls).fit()
wage_aux = sm.OLS(df["ln_wage"], controls).fit()
df["educ_resid"] = educ_aux.resid
df["wage_resid"] = wage_aux.resid
fwl = sm.OLS(df["wage_resid"], sm.add_constant(df[["educ_resid"]])).fit()

print("模型比较：")
print(comparison.round(5).to_string(index=False))
print(f"\n完整回归教育系数：{full.params['educ']:.10f}")
print(f"FWL残差回归斜率：{fwl.params['educ_resid']:.10f}")
print(f"两者差值：{full.params['educ'] - fwl.params['educ_resid']:.3e}")
print("\n变量相关系数：")
print(df[["educ", "exper", "tenure"]].corr().round(3))

# FWL三联图
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

axes[0].scatter(educ_aux.fittedvalues, df["educ"], s=14, alpha=0.35, color="#3D85C6")
lims = [df["educ"].min(), df["educ"].max()]
axes[0].plot(lims, lims, "--", color="black", linewidth=1)
axes[0].set(title="A. 从教育中剔除控制变量", xlabel="控制变量预测的教育", ylabel="实际教育")

axes[1].scatter(wage_aux.fittedvalues, df["ln_wage"], s=14, alpha=0.35, color="#E07A5F")
lims = [df["ln_wage"].min(), df["ln_wage"].max()]
axes[1].plot(lims, lims, "--", color="black", linewidth=1)
axes[1].set(title="B. 从工资中剔除控制变量", xlabel="控制变量预测的对数工资", ylabel="实际对数工资")

axes[2].scatter(df["educ_resid"], df["wage_resid"], s=14, alpha=0.35, color="#777777")
x_grid = np.linspace(df.educ_resid.min(), df.educ_resid.max(), 200)
axes[2].plot(x_grid, fwl.params["const"] + fwl.params["educ_resid"] * x_grid, color="#2A6F97", linewidth=2)
axes[2].set(title=f"C. 偏回归斜率={fwl.params['educ_resid']:.3f}", xlabel="教育残差", ylabel="工资残差")

fig.suptitle("FWL定理：先剔除相同控制变量，再比较剩余部分", fontsize=15)
fig.tight_layout()
output = OUTPUT_DIR / "ch02-fig4-fwl-partial-regression.png"
fig.savefig(output, dpi=220, bbox_inches="tight")
print(f"\n图形已保存：{output}")
