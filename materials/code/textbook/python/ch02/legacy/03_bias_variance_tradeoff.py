# # 第2章 多元线性回归：估计 — 偏差和方差权衡模拟
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：重复抽样比较完整模型、遗漏变量模型、加入高相关噪声变量模型中 x1 系数的分布。

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(20250703)

# -------- 重复抽样 --------
sims = 1000
n = 1000
records = []

for _ in range(sims):
    x1 = np.random.normal(10, 3, n)        # 练习时间
    # 让天气与练习时间正相关，使遗漏 x2 会产生可观察的遗漏变量偏误
    x2 = 5 + 0.5 * (x1 - 10) + np.random.normal(0, 2, n)
    x3 = np.random.binomial(1, 0.5, n)     # 工具质量
    x4 = x1 + np.random.normal(0, 0.1, n)  # 与 x1 高度相关的噪声变量
    u = np.random.normal(0, 1, n)
    y = 10 - 0.5 * x1 + 0.3 * x2 - 1.5 * x3 + u

    df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2, 'x3': x3, 'x4': x4})

    full = sm.OLS(df['y'], sm.add_constant(df[['x1', 'x2', 'x3']])).fit()
    omit = sm.OLS(df['y'], sm.add_constant(df[['x1', 'x3']])).fit()
    noise = sm.OLS(df['y'], sm.add_constant(df[['x1', 'x2', 'x3', 'x4']])).fit()

    records.append({
        '完整模型': full.params['x1'],
        '遗漏x2': omit.params['x1'],
        '加入高相关x4': noise.params['x1']
    })

coef = pd.DataFrame(records)
coef.describe()

# -------- 系数分布图 --------
fig, ax = plt.subplots(figsize=(9, 5))
for col, color in [('完整模型', 'tab:blue'), ('遗漏x2', 'tab:red'), ('加入高相关x4', 'tab:green')]:
    sns.kdeplot(coef[col], label=col, ax=ax, color=color)
ax.axvline(-0.5, color='black', linestyle='--', label='真实 x1 系数 = -0.5')
ax.set_title('三种模型下 x1 系数分布')
ax.set_xlabel('x1 系数')
ax.legend()
plt.show()

# -------- 均值和标准差对比 --------
summary = pd.DataFrame({
    'mean': coef.mean(),
    'std': coef.std()
})
print(summary.round(5))

# **解释提示**：真实的 x1 系数是 -0.5。比较均值是否偏离真实值，以及分布是否更分散。遗漏变量主要体现偏差，高相关噪声变量主要体现不稳定。
