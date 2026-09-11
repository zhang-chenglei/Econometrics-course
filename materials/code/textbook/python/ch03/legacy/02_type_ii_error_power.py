# # 第3章 多元线性回归：推断 — 第二类错误与检验功效模拟
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：比较不同真实效应和样本量下的拒绝比例，理解第二类错误与检验功效。

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

np.random.seed(20250705)

sims = 1000
alpha = 0.05
sample_sizes = [30, 100, 300]
betas = [0.10, 0.30, 0.50]

records = []

for n in sample_sizes:
    for beta in betas:
        rejects = 0
        for _ in range(sims):
            x = np.random.normal(size=n)
            u = np.random.normal(size=n)
            y = beta * x + u
            X = sm.add_constant(x)
            model = sm.OLS(y, X).fit()
            if model.pvalues[1] < alpha:
                rejects += 1
        power = rejects / sims
        records.append({
            'n': n,
            '真实斜率': beta,
            '检验功效': power,
            '第二类错误比例': 1 - power
        })

power_table = pd.DataFrame(records)
power_table

pivot = power_table.pivot(index='真实斜率', columns='n', values='检验功效')
pivot

fig, ax = plt.subplots(figsize=(8, 4.5))
for n in sample_sizes:
    subset = power_table[power_table['n'] == n]
    ax.plot(subset['真实斜率'], subset['检验功效'], marker='o', label=f'n={n}')

ax.set_title('效应大小、样本量与检验功效')
ax.set_xlabel('真实斜率')
ax.set_ylabel('拒绝原假设的比例')
ax.set_ylim(0, 1.05)
ax.legend()
plt.show()

# **解释提示**：真实效应越大、样本量越大，检验功效通常越高；检验功效越低，第二类错误比例越高。
