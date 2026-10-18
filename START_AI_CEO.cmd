@echo off
setlocal
cd /d "%~dp0"
where codex >nul 2>&1
if errorlevel 1 (
  echo Codex CLI is not on PATH. Install/sign in to Codex first, then run this file again.
  pause
  exit /b 1
)
if not exist "MASTER_PROMPT.md" (
  echo MASTER_PROMPT.md was not found in this folder.
  pause
  exit /b 1
)
echo Launching Codex with the AI CEO master prompt...
codex "Read MASTER_PROMPT.md in this current directory, follow all instructions, and perform the FIRST ACTION repository bootstrap yourself. Work autonomously within the safety and budget rules, only requesting native authorization when genuinely necessary."
if errorlevel 1 (
  echo Codex exited with an error. Check the output above.
)
pause
