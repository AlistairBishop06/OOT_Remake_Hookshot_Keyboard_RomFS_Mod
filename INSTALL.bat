@echo off
setlocal
cd /d "%~dp0"
set "GAME=%~1"
if not defined GAME (
  if exist "%~dp0hookshot_options.ini" set "GAME=%~dp0"
)
if not defined GAME (
  if exist "%~dp0..\hookshot_options.ini" set "GAME=%~dp0.."
)
if not defined GAME (
  echo Enter your Hookshot game folder ^(where hookshot.exe and hookshot_options.ini are^).
  set /p "GAME=Folder: "
)
if not exist "%GAME%\hookshot_options.ini" (
  echo WARNING: No hookshot_options.ini at "%GAME%".
  echo The mod can still use the standard Hookshot keybindings, but make sure you chose the game folder.
)
where py >nul 2>&1
if %errorlevel% equ 0 (
  set "PY=py -3"
) else (
  set "PY=python"
)
echo.
echo Installing Python dependencies for the keyboard prompt ROMFS patcher...
%PY% -m pip install -r "%~dp0requirements.txt" --disable-pip-version-check
if errorlevel 1 goto fail
echo.
echo Generating ROMFS mod from YOUR own game files and current Hookshot bindings...
%PY% "%~dp0build_keyboard_mod.py" --game "%GAME%"
if errorlevel 1 goto fail
echo.
echo Mod is installed. Start or restart Hookshot to see the keyboard icons.
echo To update after changing keys, run this installer again or use PLAY_WITH_KEYBOARD_PROMPTS.bat.
pause
exit /b 0
:fail
echo.
echo Could not generate the mod. Check the error above. No game or save files were changed.
pause
exit /b 1
