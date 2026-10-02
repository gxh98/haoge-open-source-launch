# 常见故障与修复

按"报什么错"查。**所有涉及凭据的操作：授权、验证码、二次验证一律交回用户本人。**

## 1. 装完 git / gh 仍然"命令找不到"

- 新装的 PATH 对已经打开的进程不生效：**重开终端**，或重启 DSH/编辑器再试。
- Windows 用 `where.exe git`、`where.exe gh` 确认真的在 PATH 里；macOS/Linux 用 `which -a`。
- 还是找不到 → 确认安装是否成功，或把安装目录手动加进 PATH。

## 2. `gh auth login` 浏览器打不开 / 卡住

- 选 `GitHub.com` → `HTTPS` → `Login with a web browser`，终端会显示**一次性验证码**；在任意设备打开 https://github.com/login/device 输入即可。
- 网络受限时先配代理再试（见第 7 条）。
- 出现密码、验证码、二次验证 → **暂停，交给用户本人**。不要要求用户把密码或 Token 发到对话里。

## 3. push 被拒：`non-fast-forward` / `rejected`

```bash
git pull --rebase origin main
git push -u origin main
```

远端有别人的提交时先 rebase。**不要用 `--force`**——会覆盖别人的提交。

## 4. 误提交了大文件（push 超时 / 报文件过大）

```bash
git rm --cached <大文件路径>
echo "<大文件路径>" >> .gitignore
git commit -m "chore: 移除误提交的大文件"
```

已经在历史里的，要用 `git filter-repo`（不是已废弃的 `filter-branch`）重写历史，再强推并通知协作者重新克隆。

## 5. 误提交了密钥（最严重）

处理顺序**绝不能颠倒**：

1. **先作废并轮换密钥** —— 去平台后台删掉这个 key、重新生成。删文件、改历史都救不回已经泄露出去的 key。
2. 再清历史：`git filter-repo --path <敏感文件> --invert-paths`
3. 强推：`git push --force --all`，并通知协作者重新克隆。
4. 仓库已公开一段时间 → 联系 GitHub Support 清理缓存与 fork。
5. 用 `python scripts/security_scan.py <项目目录>` 复扫，确认干净。

## 6. CRLF / LF 警告（Windows）

仓库根目录加 `.gitattributes`：

```
* text=auto eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
```

## 7. 国内网络：clone / push 慢或超时

```bash
# 走本地代理（端口换成你自己的）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

```bat
:: Windows cmd —— gh 也吃这个环境变量
set HTTPS_PROXY=http://127.0.0.1:7890
```

```bash
# macOS / Linux
export HTTPS_PROXY=http://127.0.0.1:7890
```

用完后清掉：`git config --global --unset http.proxy`

## 8. 公开后想改回私有

```bash
gh repo edit <user>/<repo> --visibility private --accept-visibility-change-consequences
```

注意：**已经被 fork 或克隆的内容收不回来**，改私有只挡后续访问。

## 9. `git init -b main` 报未知参数

老版本 git 不支持 `-b`：

```bash
git init && git branch -M main
```

## 10. 仓库名已被占用

`gh repo create <repo>` 会失败。换一个名字，或明确写全 `gh repo create <user>/<repo> --public --source=. --push`。

## 11. 脚本：`python` 命令不存在

- Windows 试 `py -3`；macOS/Linux 试 `python3`。
- 仍不行 → 去 https://www.python.org/downloads/ 安装，勾选"Add to PATH"。
