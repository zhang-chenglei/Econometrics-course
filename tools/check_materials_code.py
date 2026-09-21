#!/usr/bin/env python3
"""Check that the published student code is self-contained.

The scan target is the student-facing repository
(<https://github.com/zhang-chenglei/Econometrics-course-materials>), which
``tools/sync_student_repo.py`` generates from EconKB. Students download those
scripts and run them from wherever they happen to unpack them — a desktop
folder, a downloads folder, a USB stick. Two kinds of path therefore must not
appear in the code:

* absolute paths to an author's computer (``/Users/...``, ``C:\\...``, ``~/...``);
* paths that reach back into the author's repository (``图片/``, ``教材插图``
  and friends), or that assume how deep the script sits in a directory tree
  (``Path(__file__).parents[3]``).

The second group is the dangerous one: it does not raise an error, it silently
creates a new directory next to wherever the student put the file. That is how
a chapter-case script ended up writing into the textbook illustration library.

Findings are grouped by severity:

    error   breaks or pollutes a student's machine
    warn    depth-dependent; works only inside this repository's layout

`code/comprehensive_case/` 例外：该包按自身 README 的契约**必须**保留仓库目录结构
（脚本向上找到仓库根的 `data/semisynthetic/`），因此那里的深度依赖不判为 warn；
上列两条 error 级检查对它照常执行。

Usage:
    python3 tools/check_materials_code.py            # report, non-zero on error
    python3 tools/check_materials_code.py --strict   # warnings fail too
    python3 tools/check_materials_code.py --target <path to a student checkout>
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
from pathlib import Path


# Absolute locations that only exist on one person's machine.
ABSOLUTE_RE = re.compile(r"""['"](?:/Users/|/home/|[A-Za-z]:[\\/]|~/)""")

# Names of folders that live in the EconKB repository but not in the
# published package. A student's download has no such folder.
REPO_ONLY_RE = re.compile(r"""(?:图片|教材插图|小黑|封面图)""")

# `Path(__file__).parents[3]` and friends: correct only at one depth.
DEPTH_RE = re.compile(r"""parents\[\s*\d+\s*\]""")

SCAN_SUFFIXES = (".py", ".do")

# Vendored or generated trees are not maintained by hand.
SKIP_DIRS = {"__pycache__", ".ipynb_checkpoints", ".git"}

# Where the student repository is normally checked out, relative to this one.
DEFAULT_TARGET = Path(__file__).resolve().parents[1].parent / "Econometrics-course-materials"


def strip_comments(source: str, path: Path) -> str:
    """Blank out Python comments and docstrings, keeping line numbers intact.

    Comments legitimately mention ``图片/教材插图`` when they document the
    ``CASE_OUTPUT_DIR`` escape hatch, so only real code should be flagged.
    """
    lines = source.splitlines(keepends=True)
    # Character offset of the start of each line, so (row, col) can be mapped
    # back to an index into the whole source.
    line_start = [0]
    for line in lines:
        line_start.append(line_start[-1] + len(line))

    blanked = list(source)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type not in (tokenize.COMMENT, tokenize.STRING):
                continue
            (start_row, start_col), (end_row, end_col) = token.start, token.end
            if start_row != end_row:
                continue  # multi-line string: leave it alone rather than guess
            base = line_start[start_row - 1]
            for offset in range(start_col, end_col):
                blanked[base + offset] = " "
    except (tokenize.TokenError, IndentationError):
        return source  # unparseable: fall back to flagging the raw text
    return "".join(blanked)


def strip_comment_tokens(source: str) -> str:
    """只清空注释，**保留字符串字面量**。

    绝对路径只可能写在字符串里，而 `strip_comments` 连字符串一起清空——两者不能
    共用。2026-09-21 实测：`p = "/Users/feichang513/x"` 在 Python 文件里**从未被
    检出**（Stata 那侧因为不清字符串反而正常），等于这条 error 级检查对 Python
    一直是空跑。
    """
    lines = source.splitlines(keepends=True)
    line_start = [0]
    for line in lines:
        line_start.append(line_start[-1] + len(line))
    blanked = list(source)
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            (start_row, start_col), (end_row, end_col) = token.start, token.end
            if start_row != end_row:
                continue
            base = line_start[start_row - 1]
            for offset in range(start_col, end_col):
                blanked[base + offset] = " "
    except (tokenize.TokenError, IndentationError):
        return source
    return "".join(blanked)


def strip_stata_comments(source: str) -> str:
    """Blank out Stata comments. Line-based, which is enough for a path check."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("*") or stripped.startswith("//"):
            lines.append("")
        else:
            lines.append(line.split("//")[0])
    return "\n".join(lines)


def find_line(source: str, position: int) -> int:
    """1-indexed line number of a character offset."""
    return source.count("\n", 0, position) + 1


def scan(path: Path, repo: Path) -> list[tuple[str, int, str]]:
    """Return (severity, line, message) findings for one file."""
    source = path.read_text(encoding="utf-8", errors="replace")
    code = (
        strip_stata_comments(source)
        if path.suffix == ".do"
        else strip_comments(source, path)
    )

    findings: list[tuple[str, int, str]] = []

    # 绝对路径检查要**保留字符串**（路径就写在字符串里），与下面两条用的 code 不同。
    path_source = (
        strip_stata_comments(source)
        if path.suffix == ".do"
        else strip_comment_tokens(source)
    )
    for match in ABSOLUTE_RE.finditer(path_source):
        findings.append(
            ("error", find_line(path_source, match.start()), "写死的本机绝对路径")
        )

    for match in REPO_ONLY_RE.finditer(code):
        findings.append(
            (
                "error",
                find_line(code, match.start()),
                f"引用了仓库内部目录（{match.group()}）",
            )
        )

    # 综合案例包是**文档化的例外**：它的 README 明确要求保留仓库目录结构才跑得起来
    # （脚本向上走到仓库根找 `data/semisynthetic/`，学生包 README 也照此提醒），
    # 所以那里的 `parents[n]` 是包级契约的一部分，不是疏漏。**只对这条 warn 开豁免**，
    # 绝对路径与仓库内部目录两条 error 级检查照旧执行。
    depth_exempt = "comprehensive_case" in path.parts

    if not depth_exempt:
        for match in DEPTH_RE.finditer(code):
            findings.append(
                (
                    "warn",
                    find_line(code, match.start()),
                    "依赖脚本所在目录深度，换位置就跑偏",
                )
            )

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors too"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="学生仓库的本地检出目录",
    )
    args = parser.parse_args()

    repo = args.target.expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit(f"找不到学生仓库：{repo}")
    root = repo

    errors = 0
    warnings = 0
    for path in sorted(root.rglob("*")):
        if path.suffix not in SCAN_SUFFIXES or not path.is_file():
            continue
        if SKIP_DIRS & set(path.parts):
            continue

        findings = scan(path, repo)
        if not findings:
            continue

        rel = path.relative_to(repo).as_posix()
        for severity, line, message in findings:
            marker = "ERROR" if severity == "error" else "WARN "
            print(f"{marker} {rel}:{line}  {message}")
            if severity == "error":
                errors += 1
            else:
                warnings += 1

    print()
    print(f"errors: {errors}   warnings: {warnings}")
    if errors or (args.strict and warnings):
        sys.exit(1)
    print("学生版代码自包含检查通过。")


if __name__ == "__main__":
    main()
