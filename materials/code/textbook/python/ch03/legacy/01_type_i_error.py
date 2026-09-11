# # 第3章 多元线性回归：推断 — 第一类错误模拟
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：真实斜率为0时，观察5%显著性水平下的错误拒绝比例。

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(20250704)

sims = 1000
n = 50
alpha = 0.05
beta = 0.0

records = []

for _ in range(sims):
    x = np.random.normal(size=n)
    u = np.random.normal(size=n)
    y = beta * x + u
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    t_value = model.tvalues[1]
    p_value = model.pvalues[1]
    records.append({
        't_value': t_value,
        'p_value': p_value,
        'reject': p_value < alpha
    })

results = pd.DataFrame(records)
results.head()

error_count = int(results['reject'].sum())
error_rate = results['reject'].mean()

summary = pd.DataFrame({
    '重复次数': [sims],
    '显著性水平': [alpha],
    '第一类错误次数': [error_count],
    '第一类错误比例': [error_rate]
})
summary

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(results['t_value'], bins=35, color='#5b7fa6', edgecolor='white')
critical = stats.t.ppf(1 - alpha / 2, df=n - 2)
ax.axvline(-critical, color='#b23b3b', linestyle='--', linewidth=1.5)
ax.axvline(critical, color='#b23b3b', linestyle='--', linewidth=1.5)
ax.set_title('真实斜率为0时的t值分布')
ax.set_xlabel('t值')
ax.set_ylabel('次数')
plt.show()

# **解释提示**：真实斜率为0时，拒绝比例应接近设定的显著性水平。这个比例不是模型失败，而是显著性水平本身允许的第一类错误概率。
