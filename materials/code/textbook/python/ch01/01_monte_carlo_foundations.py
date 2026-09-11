"""第1章案例：从样本均值到样本回归线。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, norm

SEED = 20260910
REPS = 3000
POP_MEAN = 2.0
POP_SD = 2.0
BETA1 = 0.5

HERE = Path(__file__).resolve().parent
IMAGE_DIR = Path(__file__).resolve().parents[3] / "图片"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)

# 任务1：大数定律——累计样本均值
z = rng.exponential(scale=POP_MEAN, size=1000)
running_mean = np.cumsum(z) / np.arange(1, len(z) + 1)

# 任务2：中心极限定理——标准化样本均值
sample_sizes = [5, 30, 100]
clt_values = {}
for n in sample_sizes:
    means = rng.exponential(scale=POP_MEAN, size=(REPS, n)).mean(axis=1)
    clt_values[n] = np.sqrt(n) * (means - POP_MEAN) / POP_SD

# 任务3：OLS斜率的重复抽样分布
ols_records = []
for n in [30, 100, 500]:
    for _ in range(REPS):
        x = rng.uniform(0, 10, size=n)
        u = rng.normal(0, 1, size=n)
        y = 2 + BETA1 * x + u
        slope = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2)
        ols_records.append({"n": n, "beta1_hat": slope})

ols_results = pd.DataFrame(ols_records)
ols_summary = (
    ols_results.groupby("n")["beta1_hat"]
    .agg(mean="mean", std="std")
    .assign(bias=lambda d: d["mean"] - BETA1)
)
ols_summary.to_csv(HERE / "ch01_summary.csv", encoding="utf-8-sig")

print("累计样本均值：")
for n in [10, 100, 1000]:
    print(f"n={n:4d}: {running_mean[n - 1]:.4f}")
print("\nOLS重复抽样汇总：")
print(ols_summary.round(5))

# 汇总为一张三联图
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

axes[0].plot(np.arange(1, 1001), running_mean, color="#2A6F97", linewidth=1.4)
axes[0].axhline(POP_MEAN, color="#C44536", linestyle="--", label="总体均值=2")
axes[0].set(title="A. 大数定律", xlabel="累计样本量", ylabel="累计样本均值")
axes[0].legend(frameon=False)

x_grid = np.linspace(-3.5, 5, 500)
raw_standardized = (rng.exponential(scale=POP_MEAN, size=REPS) - POP_MEAN) / POP_SD
for values, label, color, style in [
    (raw_standardized, "原始观测", "#999999", ":"),
    (clt_values[5], "样本均值 n=5", "#E07A5F", "-"),
    (clt_values[30], "样本均值 n=30", "#3D85C6", "-"),
    (clt_values[100], "样本均值 n=100", "#2A9D8F", "-"),
]:
    axes[1].plot(x_grid, gaussian_kde(values)(x_grid), label=label, color=color, linestyle=style)
axes[1].plot(x_grid, norm.pdf(x_grid), color="black", linestyle="--", label="标准正态")
axes[1].set(title="B. 中心极限定理", xlabel="标准化数值", ylabel="密度", xlim=(-3.5, 5))
axes[1].legend(frameon=False, fontsize=8)

colors = {30: "#E07A5F", 100: "#3D85C6", 500: "#2A9D8F"}
beta_grid = np.linspace(ols_results.beta1_hat.quantile(0.002), ols_results.beta1_hat.quantile(0.998), 500)
for n in [30, 100, 500]:
    values = ols_results.loc[ols_results.n == n, "beta1_hat"]
    axes[2].plot(beta_grid, gaussian_kde(values)(beta_grid), label=f"n={n}", color=colors[n])
axes[2].axvline(BETA1, color="black", linestyle="--", label="真实斜率=0.5")
axes[2].set(title="C. OLS斜率的抽样分布", xlabel="斜率估计值", ylabel="密度")
axes[2].legend(frameon=False)

fig.suptitle("从样本均值到OLS斜率：一次完整的蒙特卡洛实验", fontsize=15)
fig.tight_layout()
output = IMAGE_DIR / "ch01-fig6-monte-carlo-foundations.png"
fig.savefig(output, dpi=220, bbox_inches="tight")
print(f"\n图形已保存：{output}")
