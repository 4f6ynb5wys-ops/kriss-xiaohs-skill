#!/usr/bin/env bash
# KRISS-xiaohs-skill 一键安装
# 装齐十站流水线需要的全部 skill：本仓库 5 个 + dbskill 9 个 + viral-writer 1 个
#
#   ./install.sh                  正常安装
#   ./install.sh --no-dbskill     跳过 dbskill（已经装过）
#   ./install.sh --no-viral       跳过 viral-writer
#   ./install.sh --dir <路径>     装到别的目录（默认 ~/.claude/skills）

set -euo pipefail

SKILLS_DIR="${HOME}/.claude/skills"
DO_DBSKILL=1
DO_VIRAL=1
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)         SKILLS_DIR="$2"; shift 2 ;;
    --no-dbskill)  DO_DBSKILL=0; shift ;;
    --no-viral)    DO_VIRAL=0; shift ;;
    -h|--help)     sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)             echo "未知参数：$1"; exit 1 ;;
  esac
done

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; }

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKED_UP=0

# 安装一个 skill 目录；已存在则先备份，绝不静默覆盖
install_skill() {
  local src="$1" name; name="$(basename "$src")"
  local dst="${SKILLS_DIR}/${name}"
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    mv "$dst" "${dst}.bak-${STAMP}"
    BACKED_UP=1
    warn "${name}（原有版本已备份为 ${name}.bak-${STAMP}）"
  else
    ok "$name"
  fi
  mkdir -p "$dst"
  cp -R "$src/." "$dst/"
}

echo
bold "KRISS-xiaohs-skill 安装"
echo "  目标目录：${SKILLS_DIR}"
echo

mkdir -p "$SKILLS_DIR"

# ── 1/3 dbskill（9 个依赖）────────────────────────────────
if [ "$DO_DBSKILL" -eq 1 ]; then
  bold "1/3  dbskill"
  if command -v npx >/dev/null 2>&1; then
    if npx -y skills add dontbesilent2025/dbskill -g --all; then
      ok "dbskill 安装完成"
    else
      fail "dbskill 安装失败，请手动执行："
      echo "      npx -y skills add dontbesilent2025/dbskill -g --all"
    fi
  else
    fail "找不到 npx（需要 Node.js）。装好 Node 后手动执行："
    echo "      npx -y skills add dontbesilent2025/dbskill -g --all"
  fi
else
  bold "1/3  dbskill —— 已跳过"
fi
echo

# ── 2/3 viral-writer（第三方）─────────────────────────────
if [ "$DO_VIRAL" -eq 1 ]; then
  bold "2/3  viral-writer（来自 nashsu/Viral_Writer_Skill）"
  if command -v git >/dev/null 2>&1; then
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    if git clone --depth 1 -q https://github.com/nashsu/Viral_Writer_Skill.git "$TMP/viral-writer" 2>/dev/null; then
      install_skill "$TMP/viral-writer"
      ok "viral-writer 安装完成"
    else
      fail "克隆失败，请手动安装：https://github.com/nashsu/Viral_Writer_Skill"
    fi
  else
    fail "找不到 git，请手动安装：https://github.com/nashsu/Viral_Writer_Skill"
  fi
else
  bold "2/3  viral-writer —— 已跳过"
fi
echo

# ── 3/3 本仓库的 5 个 skill ────────────────────────────────
bold "3/3  本仓库的 5 个 skill"
if [ ! -d "${SRC_DIR}/skills" ]; then
  fail "找不到 ${SRC_DIR}/skills —— 请在 clone 下来的仓库根目录运行本脚本"
  exit 1
fi
for d in "${SRC_DIR}"/skills/*/; do
  [ -d "$d" ] || continue
  install_skill "${d%/}"
done
echo

# ── 自检 ───────────────────────────────────────────────────
bold "自检"
MISSING=0
check() {
  if [ -f "${SKILLS_DIR}/$1/SKILL.md" ]; then
    ok "$1"
  else
    fail "$1 —— 缺失，站 $2 跑不动"
    MISSING=$((MISSING + 1))
  fi
}
check KRISS-xiaohs-skill      "全部（调度中枢）"
check benchmark-dontbesilent  "03 / 05"
check benchmark-biandao       "03 / 05"
check xhs-keyword-strategy    "07"
check xhs-note-render         "08"
check viral-writer            "06"
check dbs-goal                "01"
check dbs-benchmark           "02"
check dbs-content             "03"
check dbs-xhs-title           "05"
check dbs-resonate            "06 / 10"
check dbs-content-risk-check  "09"
check dbs-spread              "10"
check dbs-save                "存档"
check dbs-restore             "续接"

echo
if [ "$MISSING" -eq 0 ]; then
  bold "全部就绪。回到 Agent 输入：/KRISS-xiaohs-skill"
else
  bold "还缺 ${MISSING} 个，对应的站会是哑的。补齐后再跑一次本脚本即可。"
fi
if [ "$BACKED_UP" -eq 1 ]; then
  echo "同名旧目录已备份为 *.bak-${STAMP}，确认无误后可自行删除。"
fi
echo
