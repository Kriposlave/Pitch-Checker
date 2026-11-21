# Установка агента Pitch Checker для Claude (Windows).
# Запуск: правой кнопкой по файлу -> «Выполнить с помощью PowerShell»
# или в PowerShell из этой папки:  powershell -ExecutionPolicy Bypass -File .\install.ps1

param([string]$Target = (Join-Path $HOME ".claude"))

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$skills = Join-Path $Target "skills"
$agents = Join-Path $Target "agents"
New-Item -ItemType Directory -Force -Path $skills, $agents | Out-Null

$dest = Join-Path $skills "pitch-checker"
if (Test-Path $dest) {
    $backup = "$dest-backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Move-Item -LiteralPath $dest -Destination $backup
    Write-Host "Старая версия сохранена: $backup (там ваша база фактов и журнал)"
}
Copy-Item -LiteralPath (Join-Path $here "skills\pitch-checker") -Destination $skills -Recurse
foreach ($f in "fact-researcher.md", "report-verifier.md") {
    Copy-Item -LiteralPath (Join-Path $here "agents\$f") -Destination $agents -Force
}

Write-Host ""
Write-Host "Готово. Агент установлен в $Target"
$py = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if (-not $py) { Write-Host "ВНИМАНИЕ: Python не найден. Установите Python 3.9+ с python.org (отметьте «Add to PATH»)." }
Write-Host "Перезапустите Claude Desktop и откройте вкладку Code."
