@echo off
:: ============================================================
::  OpenEVSE Firmware Flasher - Windows Build Script
::  Produces:  release\OpenEVSE_Flasher-windows.zip
::  Requires:  Python 3.7+, pip
:: ============================================================
title OpenEVSE Flasher - Build

echo.
echo  OpenEVSE Firmware Flasher - Windows Build
echo  ==========================================
echo.

:: ── Check Python ─────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Install from https://www.python.org/
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Using %%v

:: ── Install / upgrade PyInstaller ────────────────────────────
echo.
echo  Installing PyInstaller...
pip install --upgrade pyinstaller --quiet
if errorlevel 1 ( echo  ERROR: pip failed. & pause & exit /b 1 )

:: ── Clean previous build ─────────────────────────────────────
if exist dist     rmdir /s /q dist
if exist build    rmdir /s /q build
if exist release  rmdir /s /q release

:: ── Build executable ─────────────────────────────────────────
echo.
echo  Building executable...
pyinstaller openevse_flasher.spec
if errorlevel 1 ( echo  ERROR: PyInstaller failed. & pause & exit /b 1 )

:: ── Assemble release folder ──────────────────────────────────
echo.
echo  Assembling release folder...
mkdir release
copy dist\OpenEVSE_Flasher.exe release\  >nul
mkdir release\avrdude
mkdir release\drivers

if exist avrdude\avrdude.exe (
    copy avrdude\avrdude.exe release\avrdude\  >nul
    echo  Bundled avrdude from local avrdude\ folder.
) else (
    echo  NOTE: avrdude\avrdude.exe not found -- add it before distributing.
)
if exist avrdude\avrdude.conf (
    copy avrdude\avrdude.conf release\avrdude\  >nul
)

if exist drivers\zadig.ini  copy drivers\zadig.ini  release\drivers\  >nul
if exist drivers\usbasp.cfg copy drivers\usbasp.cfg release\drivers\  >nul
if exist eeprom_24.bin      copy eeprom_24.bin       release\         >nul
if exist README.md          copy README.md            release\         >nul

:: ── Zip release ──────────────────────────────────────────────
echo.
echo  Creating zip...
powershell -Command "Compress-Archive -Path release\* -DestinationPath OpenEVSE_Flasher-windows.zip -Force"
if errorlevel 1 ( echo  ERROR: Zip failed. & pause & exit /b 1 )

echo.
echo  Done!  Output: OpenEVSE_Flasher-windows.zip
echo.
pause
