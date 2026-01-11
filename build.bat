@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set NAME=MummyMaze
set ENTRY=game\main.py
set ICON=game\icon.ico

echo ================================
echo Building %NAME% (onedir)
echo Root: %CD%
echo Entry: %ENTRY%
echo ================================

REM Clean old build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%NAME%.spec" del /q "%NAME%.spec"

REM Build (assets now referenced as "assets/...")
py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --name "%NAME%" ^
  --icon "%ICON%" ^
  --windowed ^
  --onedir ^
  --add-data "game\assets;assets" ^
  "%ENTRY%"

if errorlevel 1 (
  echo [ERROR] Build failed.
  pause
  exit /b 1
)

REM Hard guarantee: copy assets next to exe (matches your new paths)
if not exist "dist\%NAME%\assets" mkdir "dist\%NAME%\assets"
xcopy "game\assets" "dist\%NAME%\assets" /E /I /Y >nul

REM Save folder
if not exist "dist\%NAME%\save" mkdir "dist\%NAME%\save"

echo Done.
echo Output: dist\%NAME%\%NAME%.exe
echo Checking one sample asset:
dir "dist\%NAME%\assets\images" >nul 2>nul && echo assets\images OK || echo [WARN] assets\images missing
pause
endlocal
