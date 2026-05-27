#!/bin/bash
echo "========================================"
echo "  Сборка Insight Whisper Desktop"
echo "========================================"

if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

echo "Активация venv..."
source venv/bin/activate

echo "Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Сборка..."
pyinstaller --noconfirm --onefile --windowed \
    --name "InsightWhisper" \
    --hidden-import customtkinter \
    --hidden-import openpyxl \
    --hidden-import reportlab \
    --hidden-import matplotlib \
    --hidden-import matplotlib.backends.backend_tkagg \
    --collect-all customtkinter \
    --collect-all matplotlib \
    --collect-all reportlab \
    app.py

echo ""
echo "========================================"
echo "  Готово! Файл: dist/InsightWhisper"
echo "========================================"
