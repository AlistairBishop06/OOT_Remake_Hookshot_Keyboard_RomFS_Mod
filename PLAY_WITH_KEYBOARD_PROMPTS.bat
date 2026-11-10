@echo off
setlocal
cd /d "%~dp0"
set "GAME=%~1"
if not defined GAME if exist "%~dp0hookshot.exe" set "GAME=%~dp0"
if not defined GAME if exist "%~dp0..\hookshot.exe" set "GAME=%~dp0.."
if not defined GAME (
  echo Type the Hookshot game folder that contains hookshot.exe and hookshot_options.ini.
  set /p "GAME=Folder: "
)
if not exist "%GAME%\hookshot.exe" (
  echo hookshot.exe was not found at "%GAME%". Launch manually after installing.
  pause
  exit /b 1
)
where py >nul 2>&1
if %errorlevel% equ 0 (set "PY=py -3") else (set "PY=python")
%PY% "%~dp0build_keyboard_mod.py" --game "%GAME%"
if errorlevel 1 (
  echo Prompt rebuild failed; Hookshot has not been launched.
  pause
  exit /b 1
)
start "" "%GAME%\hookshot.exe"
exit /b 0
