#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 git / gh 是否安装、gh 是否已登录，并给出下一步该敲什么命令。

用法:
    python toolchain_check.py

退出码:
    0 = git 已装 且 gh 已装并登录
    1 = 有缺失或未登录
    2 = 运行环境异常

本脚本只检测与报告，**不会自动安装任何软件**——安装需要管理员权限，
必须由用户确认后再执行。
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

TIMEOUT = 20


def argv_for(exe: str, *args: str):
    """Windows 下 .cmd/.bat 不能被 CreateProcess 直接启动，需要包一层 cmd /c。"""
    if sys.platform == "win32" and exe.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", exe, *args]
    return [exe, *args]


def run(exe: str, *args: str):
    try:
        proc = subprocess.run(
            argv_for(exe, *args),
            capture_output=True,
            timeout=TIMEOUT,
            # 不用 text=True：它会用系统区域编码（中文 Windows 是 GBK），
            # 一旦子进程输出非 GBK 字节就会解码崩溃、结果丢失。
            encoding="utf-8",
            errors="replace",
        )
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return proc.returncode, out
    except FileNotFoundError:
        return 127, "not found"
    except Exception as exc:  # noqa: BLE001
        return 1, f"{type(exc).__name__}: {exc}"


def install_hint(tool: str) -> str:
    system = platform.system()
    if system == "Windows":
        return ("winget install --id Git.Git" if tool == "git"
                else "winget install --id GitHub.cli（或从 https://cli.github.com 下载安装包）")
    if system == "Darwin":
        return f"brew install {tool}"
    return f"用发行版包管理器安装，例如 sudo apt install {tool}"


def main() -> int:
    print("== 开源发布工具链检测 ==")
    print(f"系统: {platform.system()} {platform.release()}  Python: {platform.python_version()}")
    print("")

    git_path = shutil.which("git")
    gh_path = shutil.which("gh")
    blockers = []

    # --- git ---
    if git_path:
        code, out = run(git_path, "--version")
        if code == 0:
            print(f"[OK]   git  : {out.splitlines()[0] if out else '已安装'}")
            print(f"              路径 {git_path}")
        else:
            print(f"[WARN] git  : 找到 {git_path} 但执行失败 -> {out}")
            blockers.append("git 执行异常")
    else:
        print("[缺失] git  : 未在 PATH 中找到")
        print(f"       下一步: {install_hint('git')}")
        print("       注意: 涉及管理员权限/系统弹窗时，先向用户说明并等确认。")
        blockers.append("git 未安装")

    print("")

    # --- gh ---
    if gh_path:
        code, out = run(gh_path, "--version")
        if code == 0:
            print(f"[OK]   gh   : {out.splitlines()[0] if out else '已安装'}")
            print(f"              路径 {gh_path}")
        else:
            print(f"[WARN] gh   : 找到 {gh_path} 但执行失败 -> {out}")
            blockers.append("gh 执行异常")

        code, out = run(gh_path, "auth", "status")
        if code == 0:
            first = out.splitlines()[0] if out else "已登录"
            print(f"[OK]   登录 : {first}")
            for line in out.splitlines()[1:4]:
                if line.strip():
                    print(f"              {line.strip()}")
        else:
            print("[未登录] gh auth status 返回非零")
            for line in out.splitlines()[:4]:
                if line.strip():
                    print(f"              {line.strip()}")
            print("       下一步: gh auth login  （GitHub.com -> HTTPS -> 浏览器登录 -> 允许 gh 为 Git 配置凭据）")
            print("       注意: 浏览器授权、验证码、二次验证必须由用户本人完成；")
            print("             不要要求用户把密码或 Token 发到对话里。")
            blockers.append("gh 未登录")
    else:
        print("[缺失] gh   : 未在 PATH 中找到")
        print(f"       下一步: {install_hint('gh')}")
        print("       注意: 涉及管理员权限/系统弹窗时，先向用户说明并等确认。")
        blockers.append("gh 未安装")

    print("")
    if blockers:
        print(f"结论: {len(blockers)} 项待处理 -> {'、'.join(blockers)}")
        print("（本脚本只检测不安装；请把上面的下一步命令先给用户确认。）")
        return 1

    print("结论: git 与 gh 均就绪且已登录，可以进入发布步骤。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
