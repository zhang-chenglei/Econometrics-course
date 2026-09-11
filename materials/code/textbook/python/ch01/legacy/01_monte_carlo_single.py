# # 第1章 一元线性回归 — 蒙特卡洛模拟：单次抽样
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：生成一个 DGP 样本，估计 OLS，比较样本回归线与总体回归线

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(20250703)         # 固定随机种子，保证可复现

# -------- 生成数据 --------
n = 100                          # 样本容量
x = np.random.uniform(0, 10, n)   # X ~ Uniform(0, 10)
u = np.random.normal(0, 1, n)     # u ~ N(0, 1)
y = 2 + 0.5 * x + u               # 真实模型: Y = 2 + 0.5 X + u

df = pd.DataFrame({'x': x, 'y': y})

# -------- OLS 估计 --------
X = sm.add_constant(x)           # 添加截距项
model = sm.OLS(y, X)
results = model.fit()
print(results.summary())

# -------- 绘图：样本回归线 vs 总体回归线 --------
x_range = np.linspace(0, 10, 200)
y_true = 2 + 0.5 * x_range                         # 总体回归线
y_hat = results.params[0] + results.params[1] * x_range  # 样本回归线

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(x, y, color='gray', alpha=0.6, s=30, label='观测数据')
ax.plot(x_range, y_hat, color='blue', linewidth=2, label='样本回归线')
ax.plot(x_range, y_true, color='red', linestyle='--', linewidth=2, label='总体回归线')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('一次抽样：样本回归线 vs 总体回归线')
ax.legend()
plt.tight_layout()
plt.show()
