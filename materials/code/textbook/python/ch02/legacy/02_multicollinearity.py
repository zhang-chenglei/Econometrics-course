# # 第2章 多元线性回归：估计 — 多重共线性模拟
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：观察高度相关解释变量如何放大标准误并削弱单个系数解释。

import numpy as np
import pandas as pd
import statsmodels.api as sm

np.random.seed(20250703)

# -------- 生成数据 --------
n = 1000
x1 = np.random.normal(size=n)
x2 = x1 + 0.001 * np.random.normal(size=n)
u = np.random.normal(size=n)
y = 1 + 2 * x1 + 2 * x2 + u

df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
df[['x1', 'x2']].corr()

# -------- 同时放入高度相关变量 --------
X = sm.add_constant(df[['x1', 'x2']])
model = sm.OLS(df['y'], X).fit()
print(model.summary())

# -------- 观察条件数：越大越提示潜在共线性 --------
print('condition number:', model.condition_number)

# **解释提示**：x1 和 x2 几乎重合时，模型很难区分二者各自的独立贡献。重点观察标准误、显著性、系数方向和条件数。
