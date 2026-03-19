@echo off
cd /d "%~dp0"

echo ============================================
echo   PDF -^> LEDES 98B Converter
echo ============================================
echo.

:: Создаём .venv если его нет
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Устанавливаем зависимости
echo [2/3] Checking dependencies...
.venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Создаём папки на рабочем столе, если их нет
if not exist "%USERPROFILE%\Desktop\PDF_Input"    mkdir "%USERPROFILE%\Desktop\PDF_Input"
if not exist "%USERPROFILE%\Desktop\LEDES_Output" mkdir "%USERPROFILE%\Desktop\LEDES_Output"

echo [3/3] Starting application...
echo.
.venv\Scripts\python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
