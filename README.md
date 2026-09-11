# 中级计量经济学课程网站

本仓库发布面向应用经济学研究生的中级计量经济学课程网站。

- 网站：<https://zhang-chenglei.github.io/Econometrics-course/>
- 生成工具：Quarto
- 权威内容源：EconKB 中的中级计量课程页与共享计量教材

## 内容同步

本站内容**不在本仓库手工编辑**，全部由 EconKB 同步生成：

```bash
python3 tools/sync_from_econkb.py --econkb ~/Documents/EconKB
```

脚本读取 EconKB 中飞书课程版的 `manifest.json`（课程页导航的权威来源），生成：

| 产出 | 说明 |
|---|---|
| `index.qmd`、`course/*.qmd` | 37 个课程页 |
| `textbook/*.qmd` | 24 个教材页（含导读、附录、参考文献） |
| `assets/images/` | 页面引用的图片 |
| `_quarto.yml` 中的 AUTO-GENERATED 块 | 侧边栏导航 |
| `llms.txt` | 供 AI agent 索引的全站页面清单 |

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
