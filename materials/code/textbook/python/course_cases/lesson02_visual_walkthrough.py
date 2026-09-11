"""历史兼容文件：第2讲现已直接使用教材第2—3章的六份配套脚本。

本文件保留是为了避免旧链接失效，不再生成另一套课程数据和参考结果。
请改为运行 ``code/python/ch02/`` 与 ``code/python/ch03/`` 下的脚本。
"""

print(
    "第2讲已与教材第2—3章统一。请分别运行 code/python/ch02/ 和 "
    "code/python/ch03/ 下的六份教材脚本。"
)
raise SystemExit(0)

# %% 0. 环境与通用设置
from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output_lesson02",
        help="图片和结果表的保存目录",
    )
    return parser.parse_args()


ARGS = parse_args()
OUTPUT_DIR = ARGS.output_dir.resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["figure.dpi"] = 120
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Microsoft YaHei",
    "DejaVu Sans",
]

COLORS = {
    "orange": "#E76F51",
    "teal": "#2A9D8F",
    "blue": "#457B9D",
    "navy": "#264653",
    "sand": "#E9C46A",
    "light": "#F6F1E9",
}


def finish_figure(filename: str) -> None:
    path = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"图形已保存：{path}")


def ols(data: pd.DataFrame, variables: list[str]):
    design = sm.add_constant(data[variables])
    return sm.OLS(data["y"], design).fit()


# %% 1. 生成一份答案已知的数据
rng = np.random.default_rng(20260900)
n = 1000
x1 = rng.normal(size=n)
x2 = 0.8 * x1 + rng.normal(size=n)
u = rng.normal(loc=0, scale=2, size=n)
y = 2 + 3 * x1 + 5 * x2 + u
df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

omitted = ols(df, ["x1"])
full = ols(df, ["x1", "x2"])
n100 = ols(df.iloc[:100], ["x1", "x2"])

rx1 = sm.OLS(df["x1"], sm.add_constant(df[["x2"]])).fit().resid
ry = sm.OLS(df["y"], sm.add_constant(df[["x2"]])).fit().resid
fwl = sm.OLS(ry, rx1).fit()


# %% 2. 图1：遗漏变量会把 x1 的系数推向哪里
models = [omitted, full]
labels = ["遗漏 x₂", "控制 x₂"]
coefs = np.array([model.params["x1"] for model in models])
ses = np.array([model.bse["x1"] for model in models])
ci_half = 1.96 * ses

fig, ax = plt.subplots(figsize=(9.5, 4.8))
ypos = np.arange(len(labels))
ax.errorbar(
    coefs,
    ypos,
    xerr=ci_half,
    fmt="o",
    markersize=9,
    capsize=5,
    color=COLORS["teal"],
    ecolor=COLORS["navy"],
    linewidth=2,
)
ax.axvline(3, color=COLORS["orange"], linestyle="--", linewidth=2, label="真实系数 β₁ = 3")
for y_pos, coef, se in zip(ypos, coefs, ses):
    ax.text(coef + 0.18, y_pos, f"{coef:.3f}（SE={se:.3f}）", va="center", fontsize=11)
ax.set(
    yticks=ypos,
    yticklabels=labels,
    xlabel="x₁ 的估计系数（横线为 95% 置信区间）",
    title="同一份数据，是否控制 x₂ 会改变我们比较的对象",
    xlim=(2.2, 8.1),
)
ax.invert_yaxis()
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", alpha=0.18)
finish_figure("01_omitted_vs_full.png")


# %% 3. 图2：FWL 把“控制 x2”变成看得见的剩余关系
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.45, 1]})

axes[0].scatter(rx1, ry, s=16, alpha=0.28, color=COLORS["blue"], edgecolors="none")
grid = np.linspace(rx1.min(), rx1.max(), 200)
axes[0].plot(grid, fwl.params.iloc[0] * grid, color=COLORS["orange"], linewidth=2.5)
axes[0].axhline(0, color="#888888", linewidth=0.8)
axes[0].axvline(0, color="#888888", linewidth=0.8)
axes[0].set(
    title="剔除 x₂ 后，y 的剩余部分与 x₁ 的剩余部分",
    xlabel="x₁ 中不能被 x₂ 解释的部分",
    ylabel="y 中不能被 x₂ 解释的部分",
)
axes[0].text(
    0.04,
    0.93,
    f"剩余回归斜率 = {fwl.params.iloc[0]:.4f}",
    transform=axes[0].transAxes,
    va="top",
    bbox={"boxstyle": "round,pad=0.35", "facecolor": COLORS["light"], "edgecolor": "none"},
)

fwl_coefs = [full.params["x1"], fwl.params.iloc[0]]
axes[1].bar(
    ["完整多元回归", "FWL 剩余回归"],
    fwl_coefs,
    color=[COLORS["teal"], COLORS["sand"]],
    width=0.58,
)
axes[1].set_ylim(0, 3.55)
axes[1].set(title="两种算法得到同一个核心系数", ylabel="x₁ 的估计系数")
for i, value in enumerate(fwl_coefs):
    axes[1].text(i, value + 0.07, f"{value:.6f}", ha="center", fontsize=11)
axes[1].text(
    0.5,
    0.12,
    f"系数差 = {abs(fwl_coefs[0] - fwl_coefs[1]):.2e}",
    transform=axes[1].transAxes,
    ha="center",
    color=COLORS["navy"],
)
finish_figure("02_fwl_visual.png")


# %% 4. 图3：样本量、置信区间和两个不同的原假设
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

sample_models = [n100, full]
sample_labels = ["n = 100", "n = 1000"]
sample_coefs = np.array([model.params["x1"] for model in sample_models])
sample_ses = np.array([model.bse["x1"] for model in sample_models])
sample_y = np.arange(2)
axes[0].errorbar(
    sample_coefs,
    sample_y,
    xerr=1.96 * sample_ses,
    fmt="o",
    color=COLORS["teal"],
    ecolor=COLORS["navy"],
    capsize=5,
    linewidth=2,
    markersize=9,
)
axes[0].axvline(3, color=COLORS["orange"], linestyle="--", linewidth=2, label="真实值 3")
axes[0].set(
    yticks=sample_y,
    yticklabels=sample_labels,
    xlabel="x₁ 的估计系数",
    title="样本更多，区间通常更窄",
    xlim=(2.55, 3.85),
)
axes[0].invert_yaxis()
axes[0].legend(frameon=False)
axes[0].grid(axis="x", alpha=0.18)

estimate = full.params["x1"]
low, high = full.conf_int().loc["x1"]
axes[1].hlines(0, low, high, color=COLORS["navy"], linewidth=5, label="95% 置信区间")
axes[1].scatter([estimate], [0], s=100, color=COLORS["teal"], zorder=3, label="样本估计")
axes[1].scatter([0], [0], s=110, marker="x", linewidth=3, color=COLORS["orange"], zorder=3)
axes[1].scatter([3], [0], s=90, marker="D", color=COLORS["sand"], edgecolor=COLORS["navy"], zorder=3)
axes[1].annotate("H₀: β₁=0\n区间外：拒绝", (0, 0), xytext=(0.22, 0.24), arrowprops={"arrowstyle": "->"})
axes[1].annotate("H₀: β₁=3\n区间内：不拒绝", (3, 0), xytext=(1.75, -0.28), arrowprops={"arrowstyle": "->"})
axes[1].set(
    title="同一个估计结果，可以检验不同原假设",
    xlabel="β₁ 的可能取值",
    xlim=(-0.25, 3.6),
    ylim=(-0.48, 0.48),
    yticks=[],
)
axes[1].legend(frameon=False, loc="upper center", ncol=2, fontsize=9)
finish_figure("03_sample_size_and_tests.png")


# %% 5. 保存课堂核对表
summary = pd.DataFrame(
    {
        "model": ["omitted_n1000", "full_n1000", "fwl_n1000", "full_n100"],
        "x1_coefficient": [omitted.params["x1"], full.params["x1"], fwl.params.iloc[0], n100.params["x1"]],
        "x1_standard_error": [omitted.bse["x1"], full.bse["x1"], fwl.bse.iloc[0], n100.bse["x1"]],
    }
)
summary.to_csv(OUTPUT_DIR / "lesson02_results.csv", index=False)

test_zero = float(full.t_test("x1 = 0").pvalue)
test_true = float(full.t_test("x1 = 3").pvalue)
print("\n关键结果：")
print(summary.round(4).to_string(index=False))
print(f"H0: beta1=0 的 p 值：{test_zero:.6g}")
print(f"H0: beta1=3 的 p 值：{test_true:.4f}")
print(f"x1 的 95% 置信区间：[{low:.4f}, {high:.4f}]")
