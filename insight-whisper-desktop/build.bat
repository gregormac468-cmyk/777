@echo off
chcp 65001 > nul
echo ========================================
echo   Сборка Insight Whisper Desktop в .exe
echo ========================================
echo.

if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Активация venv...
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Сборка .exe файла...
pyinstaller --noconfirm --onefile --windowed ^
    --name "InsightWhisper" ^
    --hidden-import customtkinter ^
    --hidden-import openpyxl ^
    --hidden-import reportlab ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --collect-all customtkinter ^
    --collect-all matplotlib ^
    --collect-all reportlab ^
    app.py

echo.
echo ========================================
echo   Готово! Файл: dist\InsightWhisper.exe
echo ========================================
pause
