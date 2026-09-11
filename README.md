# 计量经济学：理论与实践

本仓库发布面向高年级本科生与研究生的计量经济学开放教材、课程讲义与可复现资源。建议学习者具备一定的统计学和多元回归分析基础。

- 网站：<https://zhang-chenglei.github.io/Econometrics-course/>
- 生成工具：Quarto
- 权威内容源：EconKB 中的中级计量课程页与共享计量教材
- 本地位置：`EconKB/30_教学/09_计量教材/GitHub课程网站/`
- 日常维护：开始修改前先阅读[维护指南](维护指南.md)

## 内容同步

课程页与教材页**不在本仓库手工编辑**，由 EconKB 同步生成：

```bash
python3 tools/sync_from_econkb.py --econkb ~/Documents/EconKB
```

脚本读取 EconKB 中飞书课程版的 `manifest.json`（课程页导航的权威来源），生成：

| 产出 | 说明 |
|---|---|
| `index.qmd`、`course/*.qmd` | 38 个飞书课程页，另有3个仓库专用页面（课件更新、代码与数据、去年基础课件） |
| `textbook/*.qmd` | 24 个教材页（含导读、附录、参考文献） |
| `assets/images/` | 页面引用的图片 |
| `_quarto.yml` 中的 AUTO-GENERATED 块 | 侧边栏导航 |
| `llms.txt` | 供 AI agent 索引的全站页面清单 |

公开代码与教学数据位于 `materials/`。其中包含教材主代码、课堂案例、AI任务卡、第11—14章综合复现代码、匿名半合成教学样本和公开政策编码；内部母表、原始年鉴及受许可约束的数据不进入公开仓库。

课程页里的飞书链接会被重写为**站内链接**；指向站外（本站未收录）的链接则还原为纯文本。

只想检查本地与 EconKB 是否有差异、不写入任何文件：

```bash
python3 tools/sync_from_econkb.py --econkb ~/Documents/EconKB --check
```

## 本地预览

```bash
quarto preview     # 带热重载
quarto render      # 生成 _site/
```

## 发布

推送到 `main` 后由 GitHub Actions 自动构建并发布到 GitHub Pages，见 `.github/workflows/publish.yml`。
