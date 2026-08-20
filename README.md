# KRISS-xiaohs-skill

十站内容流水线的调度中枢，与赛道无关。换掉目标卡就能跑另一个号。

它自己**不产出任何内容**。它做三件事：判断账号走到第几站、调度那一站该用的 skill、执行纪律层。内容由被它调度的 skill 产出。

---

## 十站

| 站 | 做什么 | 主 |
|---|---|---|
| 01 | 定位落地 → 目标卡 | `dbs-goal` |
| 02 | 找对标 → 对标包 | `dbs-benchmark` + 浏览器实采 |
| 03 | 选题 · **双轨隔离** | `benchmark-dontbesilent` / `benchmark-biandao` |
| 04 | 排期 → 发布序列 | 人工决策 |
| 05 | 起标题 · **三轨隔离** | `dbs-xhs-title` / `benchmark-biandao` / `benchmark-dontbesilent` |
| 06 | 单条成型 → 整稿 | `viral-writer`（次：`dbs-resonate`） |
| 07 | 定标签 | `xhs-keyword-strategy` |
| 08 | 出图 | `xhs-note-render` |
| 09 | 发布前排雷 | `dbs-content-risk-check` |
| 10 | 复盘回填 → 站 03 / 04 | `dbs-spread`（次：`dbs-resonate`） |

**闭环**：站 10 回填至 03 / 04。选题库是产物，不是前置条件——不要在前期建空库。

---

## 安装

复制这一行，粘到终端回车即可：

```bash
git clone https://github.com/4f6ynb5wys-ops/kriss-xiaohs-skill.git && cd kriss-xiaohs-skill && ./install.sh
```

脚本会依次装好三样东西，装完自动自检，把每一站缺什么列出来：

1. **dbskill**（9 个依赖）—— 走官方 `npx -y skills add dontbesilent2025/dbskill -g --all`
2. **viral-writer**（站 06）—— 从 [nashsu/Viral_Writer_Skill](https://github.com/nashsu/Viral_Writer_Skill) 拉取
3. **本仓库的 5 个 skill**

装完回到 Agent，输入 `/KRISS-xiaohs-skill` 就能跑。

### 安全说明

- 脚本**不会静默覆盖**你已有的 skill。同名目录会先备份成 `<名字>.bak-<时间戳>`，确认无误后自己删。
- 全部内容都在本仓库里，`install.sh` 可以先读一遍再跑。

### 可选参数

```bash
./install.sh --no-dbskill      # 已经装过 dbskill，跳过
./install.sh --no-viral        # 跳过 viral-writer
./install.sh --dir <路径>       # 装到别处（默认 ~/.claude/skills）
```

### 依赖没装全会怎样

脚本最后会逐个自检 15 个 skill。缺哪个就报哪个，并告诉你对应哪一站跑不动——**缺的站是哑的，其余站照常工作**。补齐之后重跑一次脚本即可。

---

## 依赖总表

| 来源 | skill | 用在 |
|---|---|---|
| **本仓库** | `KRISS-xiaohs-skill` | 调度中枢 |
| | `benchmark-dontbesilent` | 站 03 A 轨 · 站 05 轨 3 |
| | `benchmark-biandao` | 站 03 B 轨 · 站 05 轨 2 |
| | `xhs-keyword-strategy` | 站 07 |
| | `xhs-note-render` | 站 08 |
| **dbskill** | `dbs-goal` | 站 01 |
| | `dbs-benchmark` | 站 02 |
| | `dbs-content` | 站 03 选定后检查 |
| | `dbs-xhs-title` | 站 05 轨 1 |
| | `dbs-resonate` | 站 06 次 · 站 10 次 |
| | `dbs-content-risk-check` | 站 09 |
| | `dbs-spread` | 站 10 |
| | `dbs-save` / `dbs-restore` | 纪律 10（跨会话续接） |
| **第三方** | `viral-writer` | 站 06 主 |

**缺任何一个，对应的站就是哑的。** 缺 dbskill，站 01、02、05、09、10 全部跑不动。

---

## 用法

```
/KRISS-xiaohs-skill
```

它会先判断你走到第几站，报一行路由，然后**只执行那一站，跑完就停**。要走下一站，再说一次。

零基础起步就直接说你想做什么号，它从站 01 开始。

---

## 三条会让你意外的设计

**① 它不会替你挑。**
站 03 和站 05 是隔离多轨——多个方法论跑在互相看不见的独立上下文里，各出各的。回来之后它只分开转述，**不合并、不打分、不排名**。挑选是你的事。

这不是偷懒。两轨一旦被打分排序，隔离就白设了——融合只是延后发生。

**② 它不会替你编。**
凡是说服力来源于「这件事真的发生过」的地方（你的从业经历、真实数字、亲眼见过的案例），它一律留白，只标出位置和填充标准。AI 标插槽，人填插槽。

**③ 它会在七个地方停下来问你。**
有七项规格**故意没有定义**（见 SKILL.md 的「未决事项」）。它不许自行补齐、不许默认一个值往下跑。走到那里就停。

---

## 未决事项

以下七项尚未定义，走到需要的地方它会停下来问：

1. 站 04 排期的产出物规格
2. 站 08 出图的配色主题由谁定、出几张
3. 站 10 三个诊断 skill 的主次
4. 后端交付形态
5. 发布频率
6. 站 06–10 从未实跑，规格未经验证
7. 多轨挑选靠人、关键词双源不协调 —— **这两条是刻意设计，不是缺口，不要去「修」**

---

## 出处

- `viral-writer` 未包含在本仓库，来自 [nashsu/Viral_Writer_Skill](https://github.com/nashsu/Viral_Writer_Skill)
- `benchmark-dontbesilent` / `benchmark-biandao` 是对两位公开创作者方法论的蒸馏产物，仅供学习与内部使用
- 其余 9 个依赖来自 dbskill

---

## 换一个号要改什么

**要换**：目标卡全部字段 · 对标池关键词（含跨品类）· 插槽问题 · 平台件（非小红书则站 05–09 换件）

**不换**：十站结构 · 主次判定五条 · 纪律层十条 · 隔离多轨设计含输入切分 · 末站回环
