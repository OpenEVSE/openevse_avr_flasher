@echo off
:: ============================================================
::  OpenEVSE Firmware Flasher  -  Windows launcher
::  Double-click this file to start the app.
:: ============================================================
title OpenEVSE Firmware Flasher

:: ── Check for Python ─────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python not found!
    echo  Download and install Python 3 from https://www.python.org/downloads/
    echo  Make sure to tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Using %%v

:: ── Launch the app ───────────────────────────────────────────
echo Starting OpenEVSE Firmware Flasher...
python "%~dp0openevse_flasher.py"

if errorlevel 1 (
    echo.
    echo  The application exited with an error.
    pause
)
