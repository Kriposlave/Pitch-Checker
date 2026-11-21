#!/bin/bash
# Установка агента Pitch Checker для Claude (macOS / Linux).
# Запуск в Терминале из этой папки:  bash install.sh

set -e
TARGET="${1:-$HOME/.claude}"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$TARGET/skills" "$TARGET/agents"

DEST="$TARGET/skills/pitch-checker"
if [ -d "$DEST" ]; then
  BACKUP="$DEST-backup-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$BACKUP"
  echo "Старая версия сохранена: $BACKUP (там ваша база фактов и журнал)"
fi
cp -R "$HERE/skills/pitch-checker" "$TARGET/skills/"
cp "$HERE/agents/fact-researcher.md" "$HERE/agents/report-verifier.md" "$TARGET/agents/"

echo ""
echo "Готово. Агент установлен в $TARGET"
if ! command -v python3 >/dev/null 2>&1; then
  echo "ВНИМАНИЕ: python3 не найден. Установите: brew install python (или с python.org)."
fi
echo "Перезапустите Claude Desktop и откройте вкладку Code."
