# # 第1章 一元线性回归 — 蒙特卡洛模拟：1000次重复抽样
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：比较不同样本量下斜率估计值的偏差与精度

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style('whitegrid')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(20250703)

# -------- 参数设定 --------
N_sim = 1000      # 每种样本量的模拟次数
sample_sizes = [100, 500]
beta0_true = 2    # 真实截距
beta1_true = 0.5  # 真实斜率

records = []
for n in sample_sizes:
    for _ in range(N_sim):
        x = np.random.uniform(0, 10, n)
        u = np.random.normal(0, 1, n)
        y = beta0_true + beta1_true * x + u
        results = sm.OLS(y, sm.add_constant(x)).fit()
        records.append({'n': n, 'beta1_hat': results.params[1]})

# -------- 描述性统计 --------
sim_results = pd.DataFrame(records)
summary = sim_results.groupby('n')['beta1_hat'].agg(['mean', 'std'])
summary['bias'] = summary['mean'] - beta1_true
summary['mcse_mean'] = summary['std'] / np.sqrt(N_sim)
print(f'真实值 β₁ = {beta1_true}')
print(summary.round(6))

# -------- 直方图 --------
fig, ax = plt.subplots(figsize=(8, 5))

colors = {100: 'steelblue', 500: 'darkorange'}
for n in sample_sizes:
    values = sim_results.loc[sim_results['n'] == n, 'beta1_hat']
    sns.kdeplot(values, ax=ax, color=colors[n], linewidth=2, label=f'n={n}')

# 标注真实值
ax.axvline(beta1_true, color='darkgreen', linestyle='--', linewidth=2,
           label=f'真实值 β₁ = {beta1_true}')

ax.set_xlabel(r'斜率估计值 $\hat{\beta}_1$')
ax.set_ylabel('密度')
ax.set_title('不同样本量下斜率估计值的分布（各1000次模拟）')
ax.legend()
plt.tight_layout()
plt.show()
