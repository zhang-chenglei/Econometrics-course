# # 第4章 模型形式扩展 — 案例实践
# 配套教材：《计量经济学：理论与实践》
#
# **内容**：生成模拟工资数据，依次完成四个任务——
# 1. 水平模型 vs 对数模型
# 2. 二次项 + 极值点
# 3. 交互项 + 四群体教育回报
# 4. 四模型汇总比较

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col
import matplotlib.pyplot as plt

# ============================================================
# 数据生成
# ============================================================
np.random.seed(20250710)
n = 800

female = np.random.binomial(1, 0.48, size=n)
urban  = np.random.binomial(1, 0.55, size=n)
educ   = np.clip(np.round(np.random.normal(14, 2, size=n)), 9, 22).astype(int)
exper  = np.clip(np.round(np.random.normal(12, 6, size=n)), 0, 35).astype(int)
exper2 = exper ** 2
u = np.random.normal(0, 0.35, size=n)

ln_wage = (5.0 + 0.08*educ + 0.04*exper - 0.0006*exper2
           - 0.15*female + 0.18*urban + 0.02*educ*female
           + 0.015*educ*urban + u)
wage = np.exp(ln_wage)

df = pd.DataFrame({
    'wage': wage, 'ln_wage': ln_wage, 'educ': educ,
    'exper': exper, 'exper2': exper2,
    'female': female, 'urban': urban,
    'educ_female': educ*female, 'educ_urban': educ*urban
})
df.head()

# ============================================================
# 任务1：比较线性模型与对数模型
# ============================================================
print('========== 任务1：水平模型 vs 对数模型 ==========\n')

base_X = ['educ', 'exper', 'female', 'urban']
m_linear = sm.OLS(df['wage'], sm.add_constant(df[base_X])).fit(cov_type='HC1')
m_log    = sm.OLS(df['ln_wage'], sm.add_constant(df[base_X])).fit(cov_type='HC1')

print(f'水平模型：教育每增1年，wage 平均增加 {m_linear.params["educ"]:.2f} 元')
print(f'对数模型：教育每增1年，wage 约增加 {m_log.params["educ"]*100:.2f}%')
print()
print(summary_col([m_linear, m_log], stars=True,
                  model_names=['水平模型', '对数模型'],
                  info_dict={'N':lambda x: int(x.nobs), 'R²':lambda x: f'{x.rsquared:.3f}'}))

# ============================================================
# 任务2：检验工作经验的非线性效应
# ============================================================
print('\n========== 任务2：二次项模型 ==========\n')

X2 = sm.add_constant(df[base_X + ['exper2']])
m_quad = sm.OLS(df['ln_wage'], X2).fit(cov_type='HC1')
print(m_quad.summary())

b1, b2 = m_quad.params['exper'], m_quad.params['exper2']
turning = -b1 / (2 * b2)
print(f'经验一次项 = {b1:.5f}，平方项 = {b2:.5f}')
print(f'工资峰值的经验年限 ≈ {turning:.1f} 年')

# 绘图
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df['exper'], df['ln_wage'], alpha=0.3, color='gray', s=15)
x_range = np.linspace(0, 35, 200)
X_pred = sm.add_constant(pd.DataFrame({
    'educ': np.repeat(df['educ'].mean(), len(x_range)),
    'exper': x_range,
    'female': np.zeros(len(x_range)),
    'urban': np.ones(len(x_range)),
    'exper2': x_range**2,
}), has_constant='add')
X_pred = X_pred[m_quad.model.exog_names]
ax.plot(x_range, m_quad.predict(X_pred), color='maroon', linewidth=2, label='二次拟合')
ax.axvline(turning, color='navy', linestyle='--', label=f'峰值 ≈ {turning:.0f}年')
ax.set_xlabel('工作经验（年）'); ax.set_ylabel('对数工资')
ax.set_title('工作经验与对数工资（二次拟合）'); ax.legend()
plt.tight_layout(); plt.show()

# ============================================================
# 任务3：分析教育回报的异质性
# ============================================================
print('\n========== 任务3：交互项模型 ==========\n')

X3 = sm.add_constant(df[base_X + ['exper2', 'educ_female', 'educ_urban']])
m_inter = sm.OLS(df['ln_wage'], X3).fit(cov_type='HC1')
print(m_inter.summary())

b = m_inter.params
groups = {
    '非城市男性': b['educ'],
    '城市男性':   b['educ'] + b['educ_urban'],
    '非城市女性': b['educ'] + b['educ_female'],
    '城市女性':   b['educ'] + b['educ_female'] + b['educ_urban'],
}
print('=== 四个群体的教育回报（近似百分比） ===')
for name, val in groups.items():
    print(f'{name}: {val*100:.2f}%')

# ============================================================
# 任务4：模型比较
# ============================================================
print('\n========== 任务4：四模型汇总比较 ==========\n')

table = summary_col(
    [m_linear, m_log, m_quad, m_inter],
    stars=True,
    model_names=['水平模型', '对数模型', '+二次项', '+交互项'],
    info_dict={'N':lambda x: int(x.nobs), 'R²':lambda x: f'{x.rsquared:.3f}'},
    regressor_order=['educ', 'exper', 'exper2', 'female', 'urban',
                     'educ_female', 'educ_urban']
)
print(table)
print()
print('模型选择思考：')
print('  水平模型 → 适合讨论绝对金额变化')
print('  对数模型 → 适合讨论百分比变化，缓解右偏')
print('  +二次项  → 适合讨论边际递减趋势')
print('  +交互项  → 适合讨论群体异质性')
print('不是越复杂越好，取决于你想回答什么问题。')
