#!/bin/bash
echo "========================================"
echo "  Сборка Insight Whisper Desktop"
echo "========================================"

# Виртуальное окружение
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

echo "Активация venv..."
source venv/bin/activate

echo "Установка зависимостей..."
pip install -r requirements.txt

echo ""
echo "Сборка..."
pyinstaller --noconfirm --onefile --windowed \
    --name "InsightWhisper" \
    --add-data "config.py:." \
    --add-data "transcriber.py:." \
    --add-data "analyzer.py:." \
    --hidden-import customtkinter \
    --hidden-import openpyxl \
    --collect-all customtkinter \
    app.py

echo ""
echo "========================================"
echo "  Готово! Файл: dist/InsightWhisper"
echo "========================================"
