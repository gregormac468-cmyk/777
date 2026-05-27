@echo off
echo ========================================
echo   Сборка Insight Whisper Desktop в .exe
echo ========================================
echo.

REM Проверка виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Активация venv...
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt

echo.
echo Сборка .exe файла...
pyinstaller --noconfirm --onefile --windowed ^
    --name "InsightWhisper" ^
    --add-data "config.py;." ^
    --add-data "transcriber.py;." ^
    --add-data "analyzer.py;." ^
    --hidden-import customtkinter ^
    --hidden-import openpyxl ^
    --collect-all customtkinter ^
    app.py

echo.
echo ========================================
echo   Готово! Файл: dist\InsightWhisper.exe
echo ========================================
pause
