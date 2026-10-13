@echo off
:: ============================================================
::  OpenEVSE Firmware Flasher - Windows Build Script
::  Produces:  OpenEVSE_Flasher-windows.exe
::             (single standalone file -- no Python needed to run it;
::              avrdude and the Zadig driver installer are built in)
::  Requires:  Python 3.8+, pip
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

if not exist avrdude\avrdude.exe (
    echo  ERROR: avrdude\avrdude.exe not found.
    pause & exit /b 1
)

:: ── Install / upgrade PyInstaller ────────────────────────────
echo.
echo  Installing PyInstaller...
python -m pip install --upgrade pyinstaller --quiet
if errorlevel 1 ( echo  ERROR: pip failed. & pause & exit /b 1 )

:: ── Clean previous build ─────────────────────────────────────
if exist dist     rmdir /s /q dist
if exist build    rmdir /s /q build

:: ── Build executable ─────────────────────────────────────────
echo.
echo  Building executable...
python -m PyInstaller --noconfirm openevse_flasher.spec
if errorlevel 1 ( echo  ERROR: PyInstaller failed. & pause & exit /b 1 )

copy /y dist\OpenEVSE_Flasher.exe OpenEVSE_Flasher-windows.exe >nul

echo.
echo  Done!  Output: OpenEVSE_Flasher-windows.exe
echo.
pause
