# haoge-open-source-launch

**昊哥 · GitHub 开源发布流水线** —— 一个给 AI Agent 用的技能（DSH / Claude Skill），把本地项目从"能跑"送到"GitHub 公开可下载"。

## 为什么造它

我第一次把自己的项目开源到 GitHub 时，连 git 都不敢碰——怕泄露密钥、怕提交错、怕 README 写不像样。我搜了大量博主的发布流程，总结成规律，做成了这个技能：6 阶段 10 步，密钥体检、脱敏扫描、先报告再动手。

如果你也是第一次（或第 N 次）把项目发布到 GitHub 的开发者，这条流水线能让你少踩一遍我踩过的坑。

## 它解决什么问题

把项目开源，真正花时间的不是敲 `git push`，而是那些**容易被跳过、跳过就会出事**的环节：

- 密钥、身份证号、本地绝对路径被顺手提交进公开仓库；
- README 写了根本没实现的功能，别人照着装不上；
- 忘了加 LICENSE，别人在法务上不能用你的代码；
- 首发就报 v1.0.0，接口一变全是破窗。

这个技能把这些事固定成 **6 个阶段、10 个步骤**，每步都有**卡点**（必须停下来问用户）和**验收标准**（怎么算做完了）。

## 主要功能

- **6 阶段 10 步流程**（`SKILL.md`）：骨架 → 门面 → 体检 → 本地仓库 → GitHub 身份 → 发布
- **三条铁律**：不碰用户凭据 / 先报告再动手 / 不编造 README
- **公开前安全体检**（`scripts/security_scan.py`）：扫密钥、私钥、身份证号、本地绝对路径、临时垃圾文件，分级 BLOCKER / WARN / INFO，**输出脱敏**
- **工具链检测**（`scripts/toolchain_check.py`）：检测 git / gh 是否安装、gh 是否已登录，并给出下一步命令（**只检测，不安装**）
- **原始提示词**（`references/prompts.md`）：10 步提示词全文，可直接复制给 AI
- **故障排查**（`references/troubleshooting.md`）：11 类常见故障，含"密钥误提交"的正确处理顺序
- **三个模板**（`assets/`）：README 五节骨架、MIT 许可证全文、公开前 `.gitignore`

## 安装方法

把 `haoge-open-source-launch/` 整个目录放进你的技能目录：

```bash
git clone https://github.com/gxh98/haoge-open-source-launch.git

# DSH（Windows 下技能目录是 %USERPROFILE%\.agents\skills\）
cp -r haoge-open-source-launch ~/.agents/skills/

# Claude Code
cp -r haoge-open-source-launch ~/.claude/skills/
```

## 使用方法

装好之后不用记命令，对 AI 说触发词就行：

- 「帮我把这个项目开源」
- 「发布到 GitHub」
- 「开源前先检查一下」
- 「建个开源仓库」「上传 GitHub」「打 Release」

也可以手动跑脚本：

```bash
# 公开前体检：有 BLOCKER 时退出码为 1
python scripts/security_scan.py <项目目录>

# 机器可读输出
python scripts/security_scan.py <项目目录> --json

# git / gh 状态检测
python scripts/toolchain_check.py
```

## 输入输出示例

**输入**

```bash
python scripts/security_scan.py ./my-project
```

**输出**（示例，示意）

```
== 公开前安全体检 ==
项目      : /path/to/my-project
扫描文件  : 42 个，共 1.20 MB

-- BLOCKER (1) --
  [AI 平台令牌(sk-)] config/settings.py:7  sk-abc****6789

-- WARN (2) --
  [本地绝对路径(盘符)] README.md:12  （片段已脱敏）

结论: 发现 1 个 BLOCKER —— 禁止发布，先清理。
提示: 若该密钥曾提交过，先作废并轮换，再考虑清理 Git 历史（轮换优先于清历史）。
```

注意密钥已经脱敏，**不会明文回显**。

## 常见问题（FAQ）

**Q：它会自动改我的代码或重写 Git 历史吗？**
不会。三条铁律：不碰用户凭据 / 先报告再动手 / 不编造 README；不自动 `--force` 推送、不重写历史。

**Q：第一次用需要装什么？**
git 和 GitHub CLI（gh）。脚本只检测环境并给出下一步命令，安装（涉及管理员权限）由你确认后自己执行。

**Q：密钥已经提交过了怎么办？**
先作废并轮换密钥，再考虑清理 Git 历史——顺序不能反。`references/troubleshooting.md` 里有完整的处理步骤。

**Q：直接用 GitHub 网页上传不是更快吗？**
快，但密钥体检、LICENSE、README 与实现的一致性，这些"跳过就出事"的环节全靠自觉。这个技能把它们固定成卡点，每步有验收标准。

**Q：体检报了 BLOCKER 还能发布吗？**
不能。BLOCKER 级（密钥/私钥/身份证号）必须先清理——脚本退出码 1 就是禁止发布的信号。

## 暂不支持

- 不自动安装 git / gh —— 安装涉及管理员权限，必须由使用者确认；
- 不碰任何凭据：不索取、不记录密码与 Token；
- 不自动 `--force` 推送、不自动重写 Git 历史；
- 不做多仓库 / 组织级批量发布。

## 已测试环境

Windows 11 + Python 3.12，git 2.55.0，gh 2.100.0。

## 关于作者

**昊哥**：26 年汽车行业老兵，All in AI 的实践者。这个技能固化了我第一次把自己的项目开源到 GitHub 时的完整流程与安全检查——你再走这条路时，可以少踩一遍坑。

更多工具见[我的 GitHub 主页](https://github.com/gxh98)。

## 许可证

MIT，见 [LICENSE](LICENSE)。
