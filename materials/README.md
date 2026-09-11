# 中级计量经济学：代码与数据

本目录是课程公开复现包，面向学生和AI Agent。建议先阅读对应教材或本讲指南，再运行代码。

## 目录

- `code/textbook/python/`：教材第1—10章、课堂案例和蒙特卡洛模拟的Python代码。
- `code/textbook/stata/`：对应的Stata do-file。
- `code/textbook/ai_cards/`：各章AI任务卡。
- `code/comprehensive_case/`：第11—14章人工智能试验区综合案例复现代码。
- `data/semisynthetic/`：匿名半合成企业面板及变量说明。
- `data/policy/`：人工智能试验区公开政策事实与处理时间编码。

## Python环境

基础案例通常需要：

```bash
pip install numpy pandas scipy matplotlib statsmodels linearmodels openpyxl
```

运行单章脚本，例如：

```bash
python materials/code/textbook/python/ch07/01_panel_fe_re.py
```

完整复现第11—14章：

```bash
cd materials/code/comprehensive_case
pip install -r 共享代码/requirements.txt
python 共享代码/run_all.py
```

## Stata

第1—10章脚本多数自行生成模拟数据，可以直接打开相应do-file运行。第11—14章综合案例使用 `materials/data/semisynthetic/` 中的数据；运行前请先将Stata工作目录切换到仓库的 `materials` 文件夹。

## 交给Agent时可以这样说

> 请先阅读本目录的README和我要学习章节的AI任务卡，再检查相应代码。先解释研究问题、数据生成过程和每一步核验标准，然后指导我运行；不要直接替我编造结果。如果代码报错，请根据报错定位原因，并保留修改记录。

## 数据声明

半合成企业样本仅用于计量经济学方法教学，不能用于判断现实政策效果。政策批复信息来自公开政府文件。本站不公开包含真实企业标识的内部母表、原始年鉴或受数据库许可约束的材料。
