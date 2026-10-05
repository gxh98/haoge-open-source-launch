---
name: haoge-open-source-launch
description: 昊哥自建的「GitHub 开源发布」技能。把本地项目或技能从"能跑"送到"GitHub 公开可下载"，按 6 阶段 10 步执行：生成可开源骨架、写与真实功能一致的 README、加 LICENSE、公开前安全检查（密钥/Token/隐私/本地绝对路径/垃圾文件）、检查并安装 git 与 GitHub CLI、初始化仓库与首次提交、gh 浏览器登录、创建公开仓库并推送、打 v0.1.0 Tag 与 GitHub Release。发布全程执行中文名优先纪律：产品名=中文名（昊哥-XXX），英文仓库名仅是门牌号。触发场景：用户说"帮我把这个项目开源""发布到 GitHub""建个开源仓库""上传 GitHub""开源前先检查一下""打 Release""打 tag""gh 没装""gh 没登录""帮忙写 README/LICENSE"，或需要做公开前体检、把 skills/ 下的技能包开源发布时。
---

# 昊哥 · GitHub 开源发布流水线

把「本地能跑」变成「GitHub 公开可下载」。六个阶段、十个步骤，每步都有卡点和验收标准。

来源：得到大脑笔记《github开源skill步骤提示词-B站博主推荐》（note id `1922965037908057048`），原始 10 步提示词逐字保留在 `references/prompts.md`。

## 四条铁律（任何阶段不得违反）

1. **不碰用户凭据**：不索取、不转述、不写进任何文件。需要密码、验证码、二次验证、浏览器授权时**停下来交给用户本人**；需要管理员权限、系统弹窗、安装新包管理器时，先说明要做什么并等确认。
2. **先报告再动手**：安全检查结论、即将执行的 Git/GitHub 命令、仓库名与公开范围，先给用户看，确认后再执行。**公开不可逆**——一旦被 fork、被搜索引擎索引就收不回来。
3. **不编造**：README 必须与项目真实功能一致；信息不足就不写，不凑字数、不吹不存在的能力。
4. **中文名是产品名，英文只是门牌号**（2026-10-05 实战教训，昊哥定）：我们的客户在中文世界。对外一切触点——README 首屏标题、仓库 About 描述、Release 标题与说明、收录站提交、宣传文案——一律用中文产品名，格式「昊哥-XXX」（如「昊哥-开源skill技能猎手」）。GitHub 平台不支持中文仓库名，英文仓库名（如 `haoge-opensource-skill-hunter`）只是技术门牌号，**禁止把英文仓库名当产品名示人**。技能聚合站直接抓仓库名当大标题时，务必提交或修正为中文展示名。检验标准：站在客户角度，3 秒内能否从名字读出"谁家的 + 干什么的 + 凭啥信"。

## 阶段地图

| 阶段 | 步骤 | 产出 | 卡点（必须停下来） |
|---|---|---|---|
| A 骨架 | 1 | 项目结构 + SKILL.md | 确认功能边界与"暂不支持"清单 |
| B 门面 | 2、3 | README.md、LICENSE | README 逐条与真实功能核对 |
| C 体检 | 4 | 安全检查报告 | 有 BLOCKER 一律不许发布 |
| D 本地仓库 | 5、6 | git 仓库 + 首次提交 | 装 git 需管理员权限时；`git status` 先给用户看 |
| E GitHub 身份 | 7、8 | gh 已登录 | 浏览器授权、验证码、二次验证 |
| F 发布 | 9、10 | 公开仓库 + v0.1.0 Release | 仓库名、公开范围、命令三确认 |

## 阶段 A｜骨架（Step 1）

目标：先定"做什么、不做什么"，再动手写。

1. 向用户确认三件事：**项目解决什么问题**、**输入输出是什么**、**明确不支持什么**。信息不足就问，不要猜。
2. 生成项目结构。`scripts/` 只放真正需要复用的确定性脚本；能写进 SKILL.md 的步骤不要包成脚本。
3. 需要生成 Skill 骨架时，用 `references/prompts.md` 里的 Step 1 提示词（可直接复制给 AI）。
4. 用不同类型的真实输入各测一遍，再回头修文档。

验收：目录结构清楚；SKILL.md 里有 `name` 和 `description`；"暂不支持"清单明确；至少跑通一个真实例子。

## 阶段 B｜门面（Step 2、3）

### Step 2 README.md

用 `assets/README-template.md` 起头，五节必须写全：**解决什么问题 / 主要功能 / 安装方法 / 使用方法 / 输入输出示例**。

**首屏大标题必须用中文产品名（铁律 4）**，不写英文仓库名。

**逐条与代码核对**：写了的功能必须真的能跑；没实现的不许写。

### Step 3 LICENSE

默认 MIT：把 `assets/LICENSE-MIT.txt` 复制成项目根目录的 `LICENSE`，替换 `<YEAR>` 与 `<COPYRIGHT HOLDER>`。

需要其他许可证（Apache-2.0 / GPL 等）时，**从 https://choosealicense.com 取原文，不要凭记忆生成许可证正文**——许可证文本错一个字就有法律歧义。

提醒用户：**没有 LICENSE = 默认保留所有权利**，别人不能合法使用、修改、分发。

验收：项目根目录同时有 `README.md` 和 `LICENSE`；README 里的安装/使用步骤照着做能跑通。

## 阶段 C｜体检（Step 4）

**这是公开发布的门闸，不过不许发布。**

```bash
python scripts/security_scan.py <项目目录>
```

脚本扫描并分级：密钥/Token/私钥、个人隐私、本地绝对路径、临时与垃圾文件，输出 **BLOCKER / WARN / INFO** 三级；有 BLOCKER 时退出码非 0。输出已脱敏，不会把密钥明文打印出来。

处理规则：

- **BLOCKER（密钥、私钥、身份信息）**：立即停止发布。若该密钥**曾经提交过**，删文件没用——必须先作废并轮换密钥，再考虑用 `git filter-repo` 清理历史；已推送到公开仓库的还要联系 GitHub 支持清缓存。轮换永远排在清历史前面。
- **WARN（本地绝对路径、临时文件、大文件）**：改掉，或加进 `.gitignore`（模板见 `assets/gitignore-template.txt`）。
- **INFO**：人工判断。

**先把结论报告给用户、等确认，再执行任何 Git 操作。**

验收：脚本无 BLOCKER；`.gitignore` 覆盖 `node_modules/`、`__pycache__/`、`.env`、`*.log`、`.DS_Store` 等。

## 阶段 D｜本地仓库（Step 5、6）

### Step 5 安装 Git

```bash
python scripts/toolchain_check.py
```

没装 → 用官方方式安装（Windows `winget install --id Git.Git`；macOS `brew install git`；Linux 用发行版包管理器）。**涉及管理员权限/系统弹窗/新包管理器时，先说明再等确认**，装完重新报一次版本号。

### Step 6 初始化仓库 + 首次提交

```bash
git init -b main
git add -A
git status          # 先把这一屏给用户看
git commit -m "chore: 首次提交"
```

`git status` 的输出必须先给用户确认，避免把 `.env`、素材原片、大文件提交进去。老版本 git 不认 `-b` 时用 `git init && git branch -M main`。

验收：`git log --oneline` 有一条提交；`git status` 干净。

## 阶段 E｜GitHub 身份（Step 7、8）

### Step 7 安装 GitHub CLI

```bash
gh --version
```

没装 → Windows `winget install --id GitHub.cli`；macOS `brew install gh`。同样先等确认。

### Step 8 登录

```bash
gh auth status
gh auth login          # GitHub.com → HTTPS → 浏览器登录 → 允许 gh 为 Git 配置凭据
```

**必须由用户本人完成浏览器授权。** 出现账号密码、验证码、二次验证时暂停，把动作交给用户。

> 明确禁止：要求用户把密码或 Token 发到对话里。

授权完成后复查 `gh auth status`。

验收：`gh auth status` 显示已登录、账号正确。

## 阶段 F｜发布（Step 9、10）

### Step 9 建公开仓库 + 推送

**先把这三件事念给用户确认**：仓库名、公开范围（Public）、即将执行的命令。

确认仓库名时**一并确认 About 描述（铁律 4）**：About 必须填中文——中文产品名 + 一句话价值承诺（例：「找开源，先验活。需求先行的GitHub项目选型技能」）。英文仓库名仅作地址，不进展示层。

```bash
# 方式一：已有本地仓库
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main

# 方式二：一步到位（推荐）
gh repo create <repo> --public --source=. --remote=origin --push
```

### Step 10 版本号

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes "<发布说明>"
```

Release 的标题与发布说明**用中文写**（铁律 4）。发布说明四要素：**当前功能 / 安装方式 / 已知限制 / 下一步**。

`0.1.0` 的含义是"能用但接口可能会变"，首发不要报 `v1.0.0`。

验收：GitHub 仓库页可访问；README 正常渲染；Releases 里有 v0.1.0。

## 收尾清单（念给用户）

- 仓库地址：
- 对外展示名（中文产品名，铁律 4）：
- v0.1.0 发布页：
- 已排除的敏感文件：
- 下一步（待办 / 已知限制）：

## 配套文件

| 路径 | 用途 | 何时读 |
|---|---|---|
| `references/prompts.md` | 笔记原文 10 步提示词（可复制给 AI） | 生成骨架、写文档、做检查时 |
| `references/troubleshooting.md` | 常见故障：登录失败、推送被拒、密钥误提交、国内网络 | 命令报错时 |
| `scripts/security_scan.py` | 公开前安全体检（BLOCKER/WARN/INFO） | Step 4，每次发布前 |
| `scripts/toolchain_check.py` | git / gh 安装与登录状态检测 | Step 5、7 |
| `assets/README-template.md` | README 五节骨架 | Step 2 |
| `assets/LICENSE-MIT.txt` | MIT 许可证全文 | Step 3 |
| `assets/gitignore-template.txt` | 公开前默认忽略清单 | Step 4 |
