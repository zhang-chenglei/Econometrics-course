"""
用蒙特卡洛模拟理解计量经济学

面向零基础学生的可运行示例。脚本可在 VS Code 中按代码单元分节运行，
也可以从头到尾一次运行。所有图形和汇总结果会保存到本脚本同级的
output 文件夹中。
"""

# %% 0. 环境与通用设置
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


if "__file__" in globals():
    BASE_DIR = Path(__file__).resolve().parent
else:
    # 在 VS Code/Jupyter 逐区块运行时，__file__ 可能不存在。
    BASE_DIR = Path.cwd()

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 课堂演示时可改为 True；课后一次运行建议保持 False，避免连续弹出窗口。
SHOW_PLOTS = False

plt.rcParams["figure.dpi"] = 120
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Microsoft YaHei",
    "DejaVu Sans",
]


def finish_figure(filename: str) -> None:
    """保存当前图形，并根据设置决定是否显示。"""
    path = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    if SHOW_PLOTS:
        plt.show()
    plt.close()
    print(f"图形已保存：{path}")


def simple_ols_slope(x: np.ndarray, y: np.ndarray) -> float:
    """含截距的一元 OLS 斜率。"""
    x_centered = x - x.mean()
    return np.sum(x_centered * (y - y.mean())) / np.sum(x_centered**2)


summaries = []


# %% 1. 热身：用随机撒点估计圆周率
rng = np.random.default_rng(20260906)
n_points = 100_000
x = rng.uniform(-1, 1, n_points)
y = rng.uniform(-1, 1, n_points)
inside = x**2 + y**2 <= 1

running_pi = 4 * np.cumsum(inside) / np.arange(1, n_points + 1)
pi_hat = running_pi[-1]
print(f"圆周率估计值：{pi_hat:.5f}；真实值：{np.pi:.5f}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
show_n = 4_000
axes[0].scatter(
    x[:show_n][inside[:show_n]],
    y[:show_n][inside[:show_n]],
    s=7,
    alpha=0.55,
    color="#2A9D8F",
    label="圆内",
)
axes[0].scatter(
    x[:show_n][~inside[:show_n]],
    y[:show_n][~inside[:show_n]],
    s=7,
    alpha=0.55,
    color="#E76F51",
    label="圆外",
)
circle = plt.Circle((0, 0), 1, fill=False, color="#264653", linewidth=2)
axes[0].add_patch(circle)
axes[0].set(
    xlim=(-1.05, 1.05),
    ylim=(-1.05, 1.05),
    aspect="equal",
    title="随机撒点：圆内面积占比约为 π/4",
    xlabel="x",
    ylabel="y",
)
axes[0].legend(frameon=False)

start = 100
axes[1].plot(
    np.arange(start, n_points + 1),
    running_pi[start - 1 :],
    color="#2A9D8F",
    linewidth=1.4,
)
axes[1].axhline(np.pi, color="#E76F51", linestyle="--", label="真实值 π")
axes[1].set(
    xscale="log",
    title=f"模拟次数增加，估计逐渐稳定（最终 {pi_hat:.4f}）",
    xlabel="随机点数量（对数刻度）",
    ylabel="π 的模拟估计",
)
axes[1].legend(frameon=False)
finish_figure("01_pi_monte_carlo.png")


# %% 2. 大数定律：样本均值逐渐靠近总体均值
rng = np.random.default_rng(20260907)
true_mean = 2.0
sample = rng.exponential(scale=true_mean, size=5_000)
running_mean = np.cumsum(sample) / np.arange(1, sample.size + 1)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(sample[:200], color="#457B9D", linewidth=1)
axes[0].axhline(true_mean, color="#E63946", linestyle="--", label="总体均值 = 2")
axes[0].set(
    title="单个观测值仍然大幅波动",
    xlabel="观测序号",
    ylabel="随机变量取值",
)
axes[0].legend(frameon=False)

axes[1].plot(running_mean, color="#2A9D8F", linewidth=1.4)
axes[1].axhline(true_mean, color="#E63946", linestyle="--", label="总体均值 = 2")
axes[1].set(
    title=f"累计样本均值逐渐稳定（最终 {running_mean[-1]:.3f}）",
    xlabel="样本量 n",
    ylabel="累计样本均值",
)
axes[1].legend(frameon=False)
finish_figure("02_law_of_large_numbers.png")


# %% 3. 中心极限定理：样本均值的抽样分布逐渐接近正态
rng = np.random.default_rng(20260908)
repetitions = 5_000
sample_sizes = [1, 5, 30, 100]
true_mean = 2.0
clt_rows = []

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for ax, n in zip(axes.flat, sample_sizes):
    sample_means = rng.exponential(
        scale=true_mean, size=(repetitions, n)
    ).mean(axis=1)
    theoretical_sd = true_mean / np.sqrt(n)
    grid = np.linspace(
        max(0, sample_means.min()), sample_means.max(), 350
    )
    normal_density = (
        np.exp(-0.5 * ((grid - true_mean) / theoretical_sd) ** 2)
        / (theoretical_sd * np.sqrt(2 * np.pi))
    )
    ax.hist(
        sample_means,
        bins=45,
        density=True,
        alpha=0.72,
        color="#A8DADC",
        edgecolor="white",
    )
    ax.plot(
        grid,
        normal_density,
        color="#E63946",
        linewidth=2,
        label="对应的正态近似",
    )
    ax.axvline(
        true_mean,
        color="#264653",
        linestyle="--",
        label="总体均值 2",
    )
    ax.set(
        title=f"每次抽取 n = {n}",
        xlabel="5,000 次抽样得到的样本均值",
        ylabel="密度",
    )
    ax.legend(frameon=False, fontsize=9)
    clt_rows.append(
        {
            "案例": "中心极限定理",
            "设定": f"n={n}",
            "估计均值": sample_means.mean(),
            "模拟标准差": sample_means.std(ddof=1),
            "理论标准差": theoretical_sd,
        }
    )

fig.suptitle(
    "总体是右偏的指数分布，但样本均值的分布逐渐接近正态",
    fontsize=14,
    y=1.02,
)
finish_figure("03_central_limit_theorem.png")
summaries.append(pd.DataFrame(clt_rows))


# %% 4. 总体回归线与样本回归线：同一机制，不同样本
rng = np.random.default_rng(20260909)
n = 80
beta_0, beta_1 = 2.0, 0.5
x = rng.uniform(0, 10, n)
u = rng.normal(0, 2, n)
y = beta_0 + beta_1 * x + u

model = sm.OLS(y, sm.add_constant(x)).fit()
x_grid = np.linspace(0, 10, 200)

plt.figure(figsize=(8.5, 5.2))
plt.scatter(x, y, color="#457B9D", alpha=0.75, label="本次抽到的样本")
plt.plot(
    x_grid,
    beta_0 + beta_1 * x_grid,
    color="#E63946",
    linestyle="--",
    linewidth=2.2,
    label="总体回归线：E(y|x)=2+0.5x",
)
plt.plot(
    x_grid,
    model.params[0] + model.params[1] * x_grid,
    color="#2A9D8F",
    linewidth=2.2,
    label=f"样本回归线：ŷ={model.params[0]:.2f}+{model.params[1]:.2f}x",
)
plt.xlabel("解释变量 x")
plt.ylabel("被解释变量 y")
plt.title("样本回归线通常不会与总体回归线完全重合")
plt.legend(frameon=False)
finish_figure("04_sample_vs_population_regression.png")


# %% 5. 无偏性与精确性：重复抽样后看估计量的分布
rng = np.random.default_rng(20260910)
repetitions = 2_000
sample_sizes = [30, 100, 500]
beta_0, beta_1 = 2.0, 0.5
unbiased_rows = []
common_bins = np.linspace(-0.05, 1.05, 50)

fig, axes = plt.subplots(1, 3, figsize=(13, 4))
for ax, n in zip(axes, sample_sizes):
    beta_hats = np.empty(repetitions)
    for r in range(repetitions):
        x = rng.uniform(0, 10, n)
        u = rng.normal(0, 2, n)
        y = beta_0 + beta_1 * x + u
        beta_hats[r] = simple_ols_slope(x, y)

    mean_hat = beta_hats.mean()
    sd_hat = beta_hats.std(ddof=1)
    away_prob = np.mean(np.abs(beta_hats - beta_1) > 0.1)
    unbiased_rows.append(
        {
            "案例": "OLS无偏性与精确性",
            "设定": f"n={n}",
            "真实参数": beta_1,
            "估计均值": mean_hat,
            "偏差": mean_hat - beta_1,
            "模拟标准差": sd_hat,
            "偏离真值超过0.1的比例": away_prob,
        }
    )
    ax.hist(
        beta_hats,
        bins=common_bins,
        density=True,
        color="#A8DADC",
        edgecolor="white",
    )
    ax.axvline(
        beta_1,
        color="#E63946",
        linestyle="--",
        linewidth=2,
        label="真实参数 0.5",
    )
    ax.axvline(
        mean_hat,
        color="#264653",
        linewidth=1.8,
        label="模拟均值",
    )
    ax.set(
        title=f"n={n}\n均值={mean_hat:.3f}，标准差={sd_hat:.3f}",
        xlabel="OLS 斜率估计值",
        ylabel="密度",
        xlim=(-0.05, 1.05),
    )
    ax.legend(frameon=False, fontsize=8)

fig.suptitle(
    "估计分布围绕真实参数 0.5；样本越大，分布通常越集中",
    fontsize=14,
    y=1.03,
)
finish_figure("05_ols_unbiased_precision.png")
unbiased_summary = pd.DataFrame(unbiased_rows)
summaries.append(unbiased_summary)
print("\nOLS 无偏性与精确性：")
print(unbiased_summary.round(4).to_string(index=False))


# %% 6. 有效性：已知异方差结构时，比较 OLS 与正确加权的 WLS
rng = np.random.default_rng(20260911)
repetitions = 2_000
n = 100
true_beta = 2.0
ols_hats = np.empty(repetitions)
wls_hats = np.empty(repetitions)

for r in range(repetitions):
    x = rng.uniform(0, 10, n)
    sigma = 0.5 + 0.3 * x
    u = sigma * rng.normal(size=n)
    y = 1.0 + true_beta * x + u

    design = sm.add_constant(x)
    ols_hats[r] = sm.OLS(y, design).fit().params[1]
    wls_hats[r] = sm.WLS(y, design, weights=1 / sigma**2).fit().params[1]

efficiency_summary = pd.DataFrame(
    [
        {
            "案例": "异方差下的有效性",
            "设定": "OLS",
            "真实参数": true_beta,
            "估计均值": ols_hats.mean(),
            "偏差": ols_hats.mean() - true_beta,
            "模拟标准差": ols_hats.std(ddof=1),
        },
        {
            "案例": "异方差下的有效性",
            "设定": "正确加权的WLS",
            "真实参数": true_beta,
            "估计均值": wls_hats.mean(),
            "偏差": wls_hats.mean() - true_beta,
            "模拟标准差": wls_hats.std(ddof=1),
        },
    ]
)
summaries.append(efficiency_summary)
print("\n异方差下的有效性比较：")
print(efficiency_summary.round(4).to_string(index=False))

plt.figure(figsize=(8.5, 5.2))
common_bins = np.linspace(
    min(ols_hats.min(), wls_hats.min()),
    max(ols_hats.max(), wls_hats.max()),
    55,
)
plt.hist(
    ols_hats,
    bins=common_bins,
    density=True,
    alpha=0.55,
    color="#E9C46A",
    label=f"OLS（标准差 {ols_hats.std(ddof=1):.3f}）",
)
plt.hist(
    wls_hats,
    bins=common_bins,
    density=True,
    alpha=0.60,
    color="#2A9D8F",
    label=f"WLS（标准差 {wls_hats.std(ddof=1):.3f}）",
)
plt.axvline(true_beta, color="#E63946", linestyle="--", linewidth=2, label="真实参数 2")
plt.xlabel("斜率估计值")
plt.ylabel("密度")
plt.title("两种估计量都接近无偏，但 WLS 的抽样分布更集中")
plt.legend(frameon=False)
finish_figure("06_efficiency_ols_wls.png")


# %% 7. 遗漏变量偏误：共同原因 z 同时影响 x 与 y
rng = np.random.default_rng(20260912)
repetitions = 2_000
n = 200
true_beta_x = 3.0
beta_z = 5.0
omitted_hats = np.empty(repetitions)
full_hats = np.empty(repetitions)

for r in range(repetitions):
    z = rng.normal(size=n)
    v = rng.normal(size=n)
    x = 0.8 * z + v
    u = rng.normal(size=n)
    y = 2.0 + true_beta_x * x + beta_z * z + u

    omitted_hats[r] = simple_ols_slope(x, y)
    full_design = np.column_stack([np.ones(n), x, z])
    full_hats[r] = np.linalg.lstsq(full_design, y, rcond=None)[0][1]

ovb_summary = pd.DataFrame(
    [
        {
            "案例": "遗漏变量偏误",
            "设定": "遗漏z：y对x回归",
            "真实参数": true_beta_x,
            "估计均值": omitted_hats.mean(),
            "偏差": omitted_hats.mean() - true_beta_x,
            "模拟标准差": omitted_hats.std(ddof=1),
        },
        {
            "案例": "遗漏变量偏误",
            "设定": "控制z：y对x和z回归",
            "真实参数": true_beta_x,
            "估计均值": full_hats.mean(),
            "偏差": full_hats.mean() - true_beta_x,
            "模拟标准差": full_hats.std(ddof=1),
        },
    ]
)
summaries.append(ovb_summary)
print("\n遗漏变量偏误比较：")
print(ovb_summary.round(4).to_string(index=False))

plt.figure(figsize=(8.5, 5.2))
common_bins = np.linspace(
    min(full_hats.min(), omitted_hats.min()),
    max(full_hats.max(), omitted_hats.max()),
    65,
)
plt.hist(
    omitted_hats,
    bins=common_bins,
    density=True,
    alpha=0.62,
    color="#E76F51",
    label=f"遗漏 z（均值 {omitted_hats.mean():.2f}）",
)
plt.hist(
    full_hats,
    bins=common_bins,
    density=True,
    alpha=0.70,
    color="#2A9D8F",
    label=f"控制 z（均值 {full_hats.mean():.2f}）",
)
plt.axvline(
    true_beta_x,
    color="#264653",
    linestyle="--",
    linewidth=2,
    label="x 的真实因果效应 3",
)
plt.xlabel("x 的斜率估计值")
plt.ylabel("密度")
plt.title("遗漏共同原因 z，会让 x 与误差项相关并产生系统性偏误")
plt.legend(frameon=False)
finish_figure("07_omitted_variable_bias.png")


# %% 8. 汇总并保存数值结果
if summaries:
    summary = pd.concat(summaries, ignore_index=True, sort=False)
    summary_path = OUTPUT_DIR / "monte_carlo_summary.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"\n汇总结果已保存：{summary_path}")
else:
    print("\n尚无可汇总结果：请先运行中心极限定理及后续模拟区块。")
print("全部模拟完成。")
