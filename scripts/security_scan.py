#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公开前安全体检：扫出密钥、隐私、本地绝对路径、临时垃圾文件。

用法:
    python security_scan.py <项目目录> [--json] [--max-file-mb 2] [--big-file-mb 10]

退出码:
    0 = 无 BLOCKER，可以继续发布
    1 = 有 BLOCKER，禁止发布
    2 = 用法错误 / 目录不存在

只读脚本：不修改、不移动、不删除任何文件。输出已脱敏，不会把密钥明文打印出来。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- 配置

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".idea", ".vscode", "target", "vendor",
}

# (规则名, 正则) —— 命中即 BLOCKER
BLOCKER_CONTENT = [
    ("私钥内容", re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----")),
    ("Anthropic 令牌", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("AI 平台令牌(sk-)", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("GitHub 令牌", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}")),
    ("GitHub 细粒度令牌", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack 令牌", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("GitLab 令牌", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}")),
    ("HuggingFace 令牌", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    (
        "中国身份证号",
        re.compile(
            r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])"
            r"(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
        ),
    ),
]

# 形如 api_key = "xxxxx" 的赋值，值视作真密钥（排除占位符）
ASSIGN_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|passwd|access[_-]?key|private[_-]?key)\b"
    r"\s*[:=]\s*[\"']([^\"'\n]{12,})[\"']"
)

PLACEHOLDER_HINTS = (
    "your", "xxx", "example", "sample", "placeholder", "changeme", "change-me",
    "todo", "none", "null", "redacted", "dummy", "fake", "{{", "}}", "<", ">",
    "${", "****", "os.environ", "getenv", "process.env",
)

ENV_ASSIGN_HINTS = ("getenv", "environ", "process.env", "os.getenv", "dotenv")

ENV_OK_SUFFIXES = (".example", ".sample", ".template", ".dist", ".example.local")

BLOCKER_FILE_NAMES = {
    ".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "credentials.json", "secrets.json", ".npmrc", ".netrc", "_netrc",
    ".git-credentials", "keystore.jks",
}

BLOCKER_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".ppk")

WARN_CONTENT = [
    ("本地绝对路径(Windows 用户目录)", re.compile(r"[A-Za-z]:\\(?:Users|Documents and Settings)\\[^\s\"'<>|]*")),
    ("本地绝对路径(盘符)", re.compile(r"(?<![\w])[A-Za-z]:\\[^\s\"'<>|]{3,}")),
    ("本地绝对路径(类 Unix)", re.compile(r"/(?:Users|home)/[A-Za-z0-9._\-]{2,}(?:/[^\s\"'<>|]*)?")),
    ("邮箱地址", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
]

EMAIL_OK_HINTS = ("example.com", "example.org", "example.net", "noreply@", "no-reply@", "users.noreply.github.com")

JUNK_SUFFIXES = (".tmp", ".bak", ".swp", ".swo", ".orig", ".rej", ".log", ".pyc", "~")
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

MAX_PER_RULE_PER_FILE = 5


# ---------------------------------------------------------------- 工具函数

def mask(text: str) -> str:
    """脱敏：只保留首 6 与末 4 字符。"""
    text = text.strip()
    if len(text) <= 10:
        return "*" * len(text)
    return text[:6] + "****" + text[-4:]


def looks_like_placeholder(value: str) -> bool:
    low = value.lower()
    return any(hint in low for hint in PLACEHOLDER_HINTS)


def is_env_example(name: str) -> bool:
    return name.startswith(".env.") and name.endswith(ENV_OK_SUFFIXES)


def find_line(text: str, needle: str) -> int:
    idx = text.find(needle)
    if idx < 0:
        return 1
    return text.count("\n", 0, idx) + 1


# ---------------------------------------------------------------- 扫描

def scan_file(path: str, rel: str, findings: list, skipped: list, max_bytes: int):
    try:
        size = os.path.getsize(path)
    except OSError:
        return
    name = os.path.basename(path)

    # 凭据类文件名，直接 BLOCKER（文件名本身不是秘密，原样显示便于定位）
    env_like = name == ".env" or name.endswith(".env") or name.startswith(".env.")
    if name in BLOCKER_FILE_NAMES or name.endswith(BLOCKER_FILE_SUFFIXES) or env_like:
        if not is_env_example(name):
            findings.append(("BLOCKER", "凭据文件", rel, 1, name))
    elif name.startswith("service-account") and name.endswith(".json"):
        findings.append(("BLOCKER", "凭据文件", rel, 1, name))

    # 垃圾 / 临时文件
    if name in JUNK_NAMES or name.endswith(JUNK_SUFFIXES):
        findings.append(("WARN", "临时垃圾文件", rel, 1, mask(name)))

    if size > max_bytes:
        skipped.append(rel)
        return

    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return

    if b"\x00" in raw[:8192]:
        return

    text = raw.decode("utf-8", errors="ignore")

    # BLOCKER 内容规则
    for rule, pattern in BLOCKER_CONTENT:
        hits = 0
        for m in pattern.finditer(text):
            if hits >= MAX_PER_RULE_PER_FILE:
                break
            findings.append(("BLOCKER", rule, rel, find_line(text, m.group(0)), mask(m.group(0))))
            hits += 1

    # 密钥赋值
    hits = 0
    for m in ASSIGN_RE.finditer(text):
        if hits >= MAX_PER_RULE_PER_FILE:
            break
        value = m.group(2)
        line_text = text[text.rfind("\n", 0, m.start()) + 1: text.find("\n", m.end()) if text.find("\n", m.end()) > 0 else len(text)]
        if looks_like_placeholder(value) or any(h in line_text.lower() for h in ENV_ASSIGN_HINTS):
            continue
        findings.append(("BLOCKER", f"硬编码密钥({m.group(1)})", rel, find_line(text, m.group(0)), mask(value)))
        hits += 1

    # WARN 内容规则
    for rule, pattern in WARN_CONTENT:
        hits = 0
        for m in pattern.finditer(text):
            if hits >= MAX_PER_RULE_PER_FILE:
                break
            hit = m.group(0)
            if rule == "邮箱地址" and any(h in hit.lower() for h in EMAIL_OK_HINTS):
                continue
            findings.append(("WARN", rule, rel, find_line(text, hit), mask(hit)))
            hits += 1


def scan_tree(root: str, max_mb: float, big_mb: float) -> dict:
    findings = []
    skipped_large = []
    skipped_dirs = []
    total_files = 0
    total_bytes = 0
    max_bytes = int(max_mb * 1024 * 1024)
    big_bytes = int(big_mb * 1024 * 1024)

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        kept = []
        for d in sorted(dirnames):
            if d in SKIP_DIRS:
                skipped_dirs.append(os.path.relpath(os.path.join(dirpath, d), root))
            else:
                kept.append(d)
        dirnames[:] = kept

        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            if os.path.islink(full):
                continue
            rel = os.path.relpath(full, root)
            total_files += 1
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            total_bytes += size
            if size > big_bytes:
                findings.append(("WARN", "大文件(不该进代码仓库)", rel, 1, f"{size / 1048576:.1f} MB"))
            scan_file(full, rel, findings, skipped_large, max_bytes)

    # 根目录必备文件
    try:
        root_entries = {e.lower() for e in os.listdir(root)}
    except OSError:
        root_entries = set()
    if not any(e.startswith("readme") for e in root_entries):
        findings.append(("WARN", "根目录缺 README", ".", 1, "-"))
    if not any(e.startswith("license") or e.startswith("copying") for e in root_entries):
        findings.append(("WARN", "根目录缺 LICENSE", ".", 1, "-"))

    order = {"BLOCKER": 0, "WARN": 1}
    findings.sort(key=lambda f: (order.get(f[0], 2), f[2], f[3], f[1]))

    return {
        "root": os.path.abspath(root),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "skipped_dirs": sorted(set(skipped_dirs)),
        "skipped_large_files": skipped_large,
        "findings": findings,
    }


# ---------------------------------------------------------------- 输出

def render(result: dict) -> str:
    lines = []
    counts = {"BLOCKER": 0, "WARN": 0}
    for level, _rule, _p, _l, _s in result["findings"]:
        counts[level] = counts.get(level, 0) + 1

    lines.append("== 公开前安全体检 ==")
    lines.append(f"项目      : {result['root']}")
    lines.append(f"扫描文件  : {result['total_files']} 个，共 {result['total_bytes'] / 1048576:.2f} MB")
    if result["skipped_dirs"]:
        lines.append(f"跳过目录  : {', '.join(result['skipped_dirs'])}")
    if result["skipped_large_files"]:
        lines.append(f"超大未扫  : {len(result['skipped_large_files'])} 个（仅按体积告警）")
    lines.append("")

    for level in ("BLOCKER", "WARN"):
        items = [f for f in result["findings"] if f[0] == level]
        lines.append(f"-- {level} ({len(items)}) --")
        if not items:
            lines.append("  （无）")
        for _lv, rule, path, lineno, snippet in items:
            lines.append(f"  [{rule}] {path}:{lineno}  {snippet}")
        lines.append("")

    if counts["BLOCKER"]:
        lines.append(f"结论: 发现 {counts['BLOCKER']} 个 BLOCKER —— 禁止发布，先清理。")
        lines.append("提示: 若该密钥曾提交过，先作废并轮换，再考虑清理 Git 历史（轮换优先于清历史）。")
    else:
        lines.append(f"结论: 无 BLOCKER（{counts['WARN']} 条 WARN 请人工判断）—— 可以进入下一步。")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="公开前安全体检（只读）")
    parser.add_argument("path", help="要扫描的项目目录")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--max-file-mb", type=float, default=2.0, help="超过此体积跳过内容扫描（默认 2）")
    parser.add_argument("--big-file-mb", type=float, default=10.0, help="超过此体积告警（默认 10）")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print(f"错误: 不是有效目录: {root}", file=sys.stderr)
        return 2

    result = scan_tree(root, args.max_file_mb, args.big_file_mb)

    if args.json:
        counts = {"BLOCKER": 0, "WARN": 0}
        for level, *_rest in result["findings"]:
            counts[level] = counts.get(level, 0) + 1
        payload = dict(result)
        payload["counts"] = counts
        payload["findings"] = [
            {"level": lv, "rule": rule, "path": p, "line": ln, "snippet": s}
            for lv, rule, p, ln, s in result["findings"]
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(result))

    return 1 if any(f[0] == "BLOCKER" for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
