@echo off
title Academic Card Hub

echo ===================================================
echo   Starting Academic Card Hub (Streamlit)...
echo ===================================================
echo.

cd /d "%~dp0"

call C:\Users\Leo\anaconda3\Scripts\activate.bat

python -m streamlit run skills\academic_reading_card\scripts\card_hub_app.py

if errorlevel 1 (
    echo.
    echo [Error] Failed to start Streamlit.
    pause
)