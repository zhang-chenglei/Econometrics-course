# # 第2章 多元线性回归：估计 — 遗漏变量偏误模拟
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：比较遗漏变量模型与完整模型中 x1 系数的变化。

import numpy as np
import pandas as pd
import statsmodels.api as sm

np.random.seed(20250703)

# -------- 生成数据 --------
n = 1000
x1 = np.random.normal(size=n)
x2 = 0.8 * x1 + np.random.normal(size=n)
u = np.random.normal(size=n)
y = 2 + 3 * x1 + 5 * x2 + u

df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
df.head()

# -------- 模型1：遗漏 x2 --------
X_omit = sm.add_constant(df[['x1']])
model_omit = sm.OLS(df['y'], X_omit).fit()
print(model_omit.summary())

# -------- 模型2：完整模型 --------
X_full = sm.add_constant(df[['x1', 'x2']])
model_full = sm.OLS(df['y'], X_full).fit()
print(model_full.summary())

# -------- 系数对比 --------
compare = pd.DataFrame({
    'model': ['遗漏 x2', '完整模型'],
    'x1_coef': [model_omit.params['x1'], model_full.params['x1']],
    'x1_se': [model_omit.bse['x1'], model_full.bse['x1']],
    'r2': [model_omit.rsquared, model_full.rsquared]
})
compare

# **解释提示**：真实的 x1 系数是 3。遗漏 x2 时，x1 会吸收部分 x2 的影响，因此系数通常偏离真实值。
