# # 第3章 多元线性回归：推断 — 工资决定因素案例
# 配套教材：《计量经济学：理论与实践》
#
# **目标**：用教学模拟数据练习系数、标准误、t检验、置信区间和F检验解读。

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

np.random.seed(20250706)

# -------- 生成教学用工资数据 --------
n = 800
female = np.random.binomial(1, 0.48, size=n)
urban = np.random.binomial(1, 0.55, size=n)
educ = np.clip(np.round(np.random.normal(14, 2, size=n)), 9, 22)
exper = np.clip(np.round(np.random.normal(12, 6, size=n)), 0, 35)
exper2 = exper ** 2
ability = np.random.normal(size=n)
u = np.random.normal(0, 0.35, size=n)

ln_wage = (
    2.2 + 0.085 * educ + 0.045 * exper - 0.0008 * exper2
    - 0.120 * female + 0.180 * urban + 0.120 * ability + u
)
wage = np.exp(ln_wage)

df = pd.DataFrame({
    'wage': wage,
    'ln_wage': ln_wage,
    'educ': educ,
    'exper': exper,
    'exper2': exper2,
    'female': female,
    'urban': urban
})
df.head()

df[['wage', 'ln_wage', 'educ', 'exper', 'female', 'urban']].describe().T

# -------- 估计工资回归 --------
X = sm.add_constant(df[['educ', 'exper', 'exper2', 'female', 'urban']])
model = sm.OLS(df['ln_wage'], X).fit()
print(model.summary())

# -------- 整理核心回归表 --------
reg_table = pd.DataFrame({
    'coef': model.params,
    'std_err': model.bse,
    't_value': model.tvalues,
    'p_value': model.pvalues,
    'ci_lower': model.conf_int()[0],
    'ci_upper': model.conf_int()[1]
})
reg_table

# -------- 联合检验：工作经验及其平方项是否整体显著 --------
f_test = model.f_test('exper = 0, exper2 = 0')
print(f_test)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(df['educ'], df['ln_wage'], alpha=0.35, color='#5b7fa6')
fit = np.polyfit(df['educ'], df['ln_wage'], 1)
x_line = np.linspace(df['educ'].min(), df['educ'].max(), 100)
ax.plot(x_line, fit[0] * x_line + fit[1], color='#b23b3b', linewidth=2)
ax.set_title('教育年限与对数工资')
ax.set_xlabel('受教育年限')
ax.set_ylabel('对数工资')
plt.show()

# **解释提示**：本案例是模拟数据，用来训练推断解读。教育系数为正且显著，只能说明在这个模拟设定下存在统计关系；真实研究中还需要讨论遗漏变量、样本代表性和识别假设。
