"""
第5章 模型设定与诊断 — 案例实践

使用合成工资数据演示：
1. 遗漏变量偏误
2. 多重共线性与 VIF
3. 异方差检验与稳健标准误
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.stats.outliers_influence import variance_inflation_factor

np.random.seed(20250710)
n = 800

educ = np.clip(np.round(np.random.normal(14, 2, n)), 9, 22).astype(int)
exper = np.clip(np.round(np.random.normal(12, 6, n)), 0, 35).astype(int)
exper2 = exper**2
female = np.random.binomial(1, 0.48, n)
urban = np.random.binomial(1, 0.55, n)

# ability 与 educ 正相关，且对工资有正向影响
ability = np.random.normal(0, 1, n) + 0.3 * (educ - 14) / 2

# 两个城市变量共享潜在因子，因此高度相关
city_scale = np.random.normal(0, 1, n)
city_gdp_pc = 40000 + 15000 * city_scale + np.random.normal(0, 3000, n)
city_pop = 400 + 150 * city_scale + np.random.normal(0, 30, n)

# 误差标准差随工作经验上升
u = np.random.normal(0, np.sqrt(0.2 + 0.03 * exper), n)
ln_wage = (
    5.0 + 0.08 * educ + 0.04 * exper - 0.0006 * exper2
    - 0.15 * female + 0.18 * urban + 0.05 * ability
    + 0.000005 * city_gdp_pc + 0.0001 * city_pop + u
)

df = pd.DataFrame({
    'ln_wage': ln_wage,
    'educ': educ,
    'exper': exper,
    'exper2': exper2,
    'female': female,
    'urban': urban,
    'ability': ability,
    'city_gdp_pc': city_gdp_pc,
    'city_pop': city_pop,
})

print(f'样本量: {len(df)}')

# ============================================================
# 任务1：遗漏变量偏误
# ============================================================
base_vars = [
    'educ', 'exper', 'exper2', 'female', 'urban',
    'city_gdp_pc', 'city_pop',
]
m_naive = sm.OLS(
    df['ln_wage'], sm.add_constant(df[base_vars])
).fit(cov_type='HC1')
m_full = sm.OLS(
    df['ln_wage'], sm.add_constant(df[base_vars + ['ability']])
).fit(cov_type='HC1')

coef_comparison = pd.DataFrame({
    'model': ['遗漏 ability', '控制 ability'],
    'educ_coef': [m_naive.params['educ'], m_full.params['educ']],
    'educ_se': [m_naive.bse['educ'], m_full.bse['educ']],
})
print('\n===== 遗漏变量诊断 =====')
print(coef_comparison.round(5).to_string(index=False))

# ============================================================
# 任务2：多重共线性
# ============================================================
vif_vars = [
    'educ', 'exper', 'exper2', 'female', 'urban',
    'city_gdp_pc', 'city_pop', 'ability',
]
X_vif = sm.add_constant(df[vif_vars])
vif_table = pd.DataFrame({
    'variable': X_vif.columns,
    'VIF': [
        variance_inflation_factor(X_vif.values, i)
        for i in range(X_vif.shape[1])
    ],
})
print('\n===== VIF =====')
print(vif_table.round(3).to_string(index=False))

# ============================================================
# 任务3：异方差检验与稳健标准误
# ============================================================
diagnostic_vars = [
    'educ', 'exper', 'exper2', 'female', 'urban',
    'city_gdp_pc', 'ability',
]
X_diag = sm.add_constant(df[diagnostic_vars])
m_conventional = sm.OLS(df['ln_wage'], X_diag).fit()
m_robust = sm.OLS(df['ln_wage'], X_diag).fit(cov_type='HC1')

bp = het_breuschpagan(m_conventional.resid, X_diag)
white = het_white(m_conventional.resid, X_diag)
test_table = pd.DataFrame({
    'test': ['Breusch-Pagan LM', 'White LM'],
    'statistic': [bp[0], white[0]],
    'p_value': [bp[1], white[1]],
})
se_comparison = pd.DataFrame({
    'coef': m_conventional.params,
    'conventional_se': m_conventional.bse,
    'robust_se_HC1': m_robust.bse,
})

print('\n===== 异方差检验 =====')
print(test_table.round(5).to_string(index=False))
print('\n===== 标准误比较 =====')
print(se_comparison.round(5).to_string())

print('\n解释边界：稳健标准误修正推断，不会修复遗漏变量偏误。')
