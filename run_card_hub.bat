@echo off
title Academic Card Hub

echo ===================================================
echo   Starting Academic Card Hub (Streamlit)...
echo ===================================================
echo.

cd /d "%~dp0"

rem 優先啟用集中式虛擬環境 thesis_env
if exist "%USERPROFILE%\.venvs\thesis_env\Scripts\activate.bat" (
    call "%USERPROFILE%\.venvs\thesis_env\Scripts\activate.bat"
) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
) else if exist "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" (
    call "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
) else if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
    call "C:\ProgramData\anaconda3\Scripts\activate.bat"
) else if exist "C:\anaconda3\Scripts\activate.bat" (
    call "C:\anaconda3\Scripts\activate.bat"
)

set PYTHONDONTWRITEBYTECODE=1
python -B -m streamlit run skills\academic_reading_card\scripts\card_hub_app.py

if errorlevel 1 (
    echo.
    echo [Error] Failed to start Streamlit.
    pause
)
