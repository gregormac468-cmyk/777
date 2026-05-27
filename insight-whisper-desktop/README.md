# Insight Whisper Desktop

Десктопное приложение для транскрибации аудиозвонков и AI-анализа качества работы менеджеров.

## Возможности

- **Транскрибация аудио** — через OpenAI Whisper или Google Gemini
- **AI-анализ звонков** — через 5 провайдеров (Google, OpenAI, DeepSeek, Anthropic, Qwen)
- **Пользовательские инструкции** — загрузка критериев оценки из текстовых файлов
- **Пакетная обработка** — загрузка нескольких файлов с паузой между ними
- **Экспорт результатов** — в Excel (.xlsx) и JSON
- **Тёмная/светлая тема**
- **Автосохранение результатов**

## Быстрый старт (без сборки в .exe)

### 1. Установите Python 3.10+

Скачайте с [python.org](https://www.python.org/downloads/)

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Запустите

```bash
python app.py
```

### 4. Настройте API ключи

Перейдите во вкладку **Настройки** и введите API ключ выбранного провайдера:
- **Google Gemini** (рекомендуется): [aistudio.google.com](https://aistudio.google.com/apikey)
- **OpenAI**: [platform.openai.com](https://platform.openai.com/api-keys)
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Qwen**: [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)

## Сборка в .exe

### Windows:

```
build.bat
```

Или вручную:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "InsightWhisper" --hidden-import customtkinter --hidden-import openpyxl --collect-all customtkinter app.py
```

Готовый файл будет в папке `dist/InsightWhisper.exe`

### Linux/macOS:

```bash
chmod +x build.sh
./build.sh
```

## Структура проекта

```
insight-whisper-desktop/
├── app.py              # Главный файл с GUI
├── config.py           # Модуль конфигурации
├── transcriber.py      # Модуль транскрибации
├── analyzer.py         # Модуль AI-анализа
├── requirements.txt    # Зависимости Python
├── build.bat           # Скрипт сборки Windows
├── build.sh            # Скрипт сборки Linux/Mac
└── README.md           # Документация
```

## Как пользоваться

1. **Настройки** — введите API ключ, выберите провайдера и модель
2. **Инструкции** — создайте или загрузите инструкцию с критериями оценки
3. **Загрузка** — выберите аудиофайлы, укажите менеджера, нажмите "Начать анализ"
4. **Результаты** — просмотрите оценки, экспортируйте в Excel

## Поддерживаемые аудио-форматы

mp3, wav, m4a, ogg, oga, aac, flac, webm, mp4, opus, amr, 3gp

## Конфигурация

Настройки хранятся в: `~/.insight-whisper/config.json`
Инструкции: `~/.insight-whisper/instructions/`
Результаты: `~/.insight-whisper/results/`

## Модели по умолчанию

| Провайдер | Транскрибация | Анализ |
|-----------|--------------|--------|
| Google    | gemini-2.5-flash | gemini-2.5-flash |
| OpenAI    | whisper-1 | gpt-4o-mini |
| DeepSeek  | — | deepseek-chat |
| Anthropic | — | claude-3-5-sonnet-latest |
| Qwen      | — | qwen-plus |

> DeepSeek, Anthropic и Qwen не поддерживают транскрибацию аудио, только анализ текста.
