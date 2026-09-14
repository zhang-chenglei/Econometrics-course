#!/usr/bin/env python3
"""Generate the student-facing code repository from the EconKB sources.

EconKB keeps the teaching code in a layout that mirrors how it is maintained:

    code/
      python/ch01/01_monte_carlo_foundations.py
      python/ch01/legacy/01_monte_carlo_single.py
      stata/ch01/01_monte_carlo_foundations.do
      ai_cards/ch01_ai_task_card.md
      comprehensive_case/第11章/代码/ch11_research_design.py

Every folder there earns its keep for whoever maintains the material, and none
of it helps a student, who wants "the chapter I am on, and the two files I
actually run". This script writes a second, deliberately dull repository:

    README.md
    第1章_一元线性回归/
      python/01_monte_carlo_foundations.py
      stata/01_monte_carlo_foundations.do
      AI任务卡.md
    第11-14章_综合案例/...
    数据/...

Rules the student repo relies on:

* no `legacy/`, no maintenance notes, no website tooling — only what a student
  is meant to open;
* the scripts themselves are byte-identical to the EconKB originals, so the two
  stay in step by construction rather than by discipline;
* running the script is the only way to change the target; hand edits there are
  drift and get reported by ``--check``.

Usage:
    python3 tools/sync_student_repo.py --econkb ~/Documents/EconKB \\
        --target <checkout of Econometrics-course-materials>
    python3 tools/sync_student_repo.py ... --check    # report drift, write nothing
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


# EconKB chapter directory -> student-facing folder name. Chapter titles match
# the textbook (`30_教学/09_计量教材/拆分章节/`).
CHAPTERS: list[tuple[str, str]] = [
    ("ch01", "第1章_一元线性回归"),
    ("ch02", "第2章_多元线性回归_估计"),
    ("ch03", "第3章_多元线性回归_推断"),
    ("ch04", "第4章_模型形式扩展"),
    ("ch05", "第5章_模型设定与诊断"),
    ("ch06", "第6章_离散选择模型"),
    ("ch07", "第7章_面板数据模型"),
    ("ch08", "第8章_工具变量模型"),
    ("ch09", "第9章_因果推断前沿方法"),
]

# Copied wholesale, keeping their internal layout: these are self-contained
# reproduction packages whose scripts locate each other by relative path, so
# flattening them would break `共享代码/run_all.py`.
BULK_DIRS: list[tuple[str, str]] = [
    ("comprehensive_case", "第11-14章_综合案例"),
]

# Small teaching datasets, copied from this repository rather than EconKB
# (EconKB holds the multi-hundred-MB working data, which is not public).
DATA_DIRS: list[tuple[str, str]] = [
    ("semisynthetic", "数据/半合成教学数据"),
    ("policy", "数据/人工智能试验区政策数据"),
]

SKIP_DIR_NAMES = {"__pycache__", ".ipynb_checkpoints"}

# Running a script writes its figures and tables next to itself, so a student
# who keeps the checkout under git would otherwise see a dirty tree forever.
GITIGNORE = """# 脚本运行后在脚本同级生成的图和结果表，不需要提交
output/
__pycache__/
.ipynb_checkpoints/
"""

README = """# 计量经济学：理论与实践｜课程代码与数据

这里是本课程公开使用的全部代码与数据，**按教材章节组织**。找到你要学的那一章，
进去跑里面的 Python 或 Stata 文件即可。

## 下载

- **下载全部**：点本页右上角绿色的 `Code` 按钮 → `Download ZIP`
- **只取一章**：点进对应章的文件夹，单独下载里面的文件

## 目录

每章文件夹里固定三样东西：

| 内容 | 说明 |
|------|------|
| `python/` | 该章的 Python 脚本 |
| `stata/` | 该章的 Stata do-file，与 Python 版一一对应 |
| `AI任务卡.md` | 可直接交给 AI Agent，按「目标—步骤—核验—解释」完成练习 |

另有：

| 文件夹 | 内容 |
|--------|------|
| `第11-14章_综合案例/` | 人工智能试验区综合案例复现包，含 Python、Stata、Jupyter Notebook 三版 |
| `数据/` | 半合成教学样本、人工智能试验区政策数据 |

## 运行

每个脚本都是**独立的**：下载到桌面、下载文件夹或任何位置都能直接运行，
不需要改动脚本里的路径。

**Python**

```bash
pip install numpy pandas scipy matplotlib statsmodels linearmodels
python 第2章_多元线性回归_估计/python/01_controls_ovb.py
```

**Stata**：打开对应的 `.do` 文件直接运行。

运行结果在哪里：

- 第1—5章的脚本会把图和结果表保存到**脚本同级的 `output/` 文件夹**；
- 第6—9章的脚本直接在终端打印结果；
- 第11—14章综合案例需要**进入该文件夹**后再运行（它的各章脚本互相引用）。

## 数据说明

- 全部为教学用合成数据，真实参数由数据生成过程人为设定。它适合检查方法、
  练习操作，**不代表现实中的经济效果或政策效果**。
- 综合案例中的企业样本已匿名化，其中的效应也是人为植入的，
  不得用于评价现实政策。
- 引用教学数据时请标注“半合成教学数据”。

## 遇到问题

1. 看报错的最后一行缺少哪个包，`pip install` 装上即可；
2. 确认运行目录——第11—14章综合案例要先进入该文件夹再运行；
3. 仍然解决不了，把「报错信息 + 你运行的命令 + 你在哪一章」发给任课教师。

## 相关链接

- 课程网站：<https://zhang-chenglei.github.io/Econometrics-course/>
- 教材与讲义：见课程网站「教材全文」栏目
"""


def plan(econkb: Path, repo: Path) -> dict[Path, Path]:
    """Map every target file to the source it should come from."""
    expected: dict[Path, Path] = {}
    src = econkb / "30_教学/09_计量教材/code"

    for chapter, folder in CHAPTERS:
        for language, suffix in (("python", ".py"), ("stata", ".do")):
            # Match the extension rather than everything in the folder: authors
            # run these scripts in place, so the directory also holds whatever
            # the last run wrote (`ch01_summary.csv`, `*.log`) — outputs are not
            # source and must not ship to students.
            for path in sorted((src / language / chapter).glob(f"*{suffix}")):
                if path.is_file():
                    expected[repo / folder / language / path.name] = path
        card = src / "ai_cards" / f"{chapter}_ai_task_card.md"
        if card.is_file():
            expected[repo / folder / "AI任务卡.md"] = card

    for source_dir, target_dir in BULK_DIRS:
        root = src / source_dir
        for path in sorted(root.rglob("*")):
            if path.is_file() and not SKIP_DIR_NAMES & set(path.parts):
                expected[repo / target_dir / path.relative_to(root)] = path

    # The teaching datasets live in this site repository, not in EconKB, whose
    # own `案例数据/` is the multi-hundred-MB working set and stays unpublished.
    site_data = Path(__file__).resolve().parents[1] / "materials" / "data"
    for source_dir, target_dir in DATA_DIRS:
        root = site_data / source_dir
        for path in sorted(root.rglob("*")):
            if path.is_file() and not SKIP_DIR_NAMES & set(path.parts):
                expected[repo / target_dir / path.relative_to(root)] = path

    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--econkb", type=Path, required=True, help="EconKB checkout")
    parser.add_argument("--target", type=Path, required=True, help="student repo checkout")
    parser.add_argument("--check", action="store_true", help="report drift only")
    args = parser.parse_args()

    econkb = args.econkb.expanduser().resolve()
    repo = args.target.expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit(f"目标不是目录：{repo}")

    expected = plan(econkb, repo)

    if args.check:
        problems = []
        for target, source in expected.items():
            if not target.exists():
                problems.append(f"缺失  {target.relative_to(repo)}")
            elif not filecmp.cmp(source, target, shallow=False):
                problems.append(f"内容不同 {target.relative_to(repo)}")
        # Anything in the repo that is neither generated nor README is drift:
        # a student-facing folder should never accumulate hand-made files.
        known = set(expected) | {repo / "README.md", repo / ".gitignore"}
        for path in sorted(repo.rglob("*")):
            if path.is_file() and ".git" not in path.parts and path not in known:
                problems.append(f"多余文件 {path.relative_to(repo)}")
        if problems:
            print(f"{len(problems)} 处与 EconKB 不一致：")
            for problem in problems:
                print(f"  {problem}")
            sys.exit(1)
        print(f"一致：{len(expected)} 个文件与 EconKB 同步。")
        return

    written: list[Path] = []
    for target, source in expected.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or not filecmp.cmp(source, target, shallow=False):
            shutil.copy2(source, target)
        written.append(target)

    # Prune orphans. A file that is no longer generated has been retired from
    # the student set (moved to `legacy/`, renamed, or dropped upstream), and
    # leaving it behind would quietly keep shipping something the sources no
    # longer declare. Only folders this script owns are touched — a student's
    # own notes elsewhere in the checkout are none of its business.
    managed = {folder.split("/")[0] for _chapter, folder in CHAPTERS}
    managed |= {folder.split("/")[0] for _source, folder in BULK_DIRS}
    managed |= {folder.split("/")[0] for _source, folder in DATA_DIRS}
    keep = set(expected) | {repo / "README.md", repo / ".gitignore"}
    removed: list[str] = []
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path in keep:
            continue
        if path.relative_to(repo).parts[0] in managed:
            path.unlink()
            removed.append(path.relative_to(repo).as_posix())

    (repo / "README.md").write_text(README, encoding="utf-8")
    (repo / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    print(f"写入 {len(written)} 个文件 + README.md → {repo}")
    if removed:
        print(f"移除 {len(removed)} 个已不再生成的旧文件：")
        for path in removed:
            print(f"  - {path}")
    folders = sorted({path.relative_to(repo).parts[0] for path in written})
    for folder in folders:
        count = sum(1 for path in written if path.relative_to(repo).parts[0] == folder)
        print(f"  {folder}  ({count} 个文件)")


if __name__ == "__main__":
    main()
